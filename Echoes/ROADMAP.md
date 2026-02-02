# Echoes — Roadmap Backend

## Étape 0 — Migration Alembic

Les 3 nouveaux modèles (`PlayerEquipmentLoadout`, `CombatSession`, `CombatLog`) et les modifications sur `Monster`/`Spell` ne sont pas encore en DB.

### Fichiers concernés
- `backend/alembic/env.py` — vérifier que tous les modèles sont importés pour que Alembic les détecte
- Il faut que `env.py` importe `app.models.loadout`, `app.models.combat_session`, `app.models.combat_log`, `app.models.enums`

### Commandes
```bash
cd backend
alembic revision --autogenerate -m "add loadout, combat_session, combat_log, enrich monster and spell"
alembic upgrade head
```

### Ce que ça va créer/modifier en DB
- **Nouvelle table** `player_equipment_loadout` (7 colonnes de slots)
- **Nouvelle table** `combat_sessions` (état du combat persisté)
- **Nouvelle table** `combat_logs` (logs structurés)
- **Sur `monsters`** : nouvelles colonnes `description`, `is_boss`, `ai_behavior`, `ability_power`, `armor`, `magic_resistance`, `speed`, `scaling_hp/ad/armor`, `abilities`, `reward_gold_min`, `reward_gold_max`, `sprite_key`. L'ancienne colonne `reward_gold` et `metadata_props` devront être migrées/supprimées.
- **Sur `spells`** : nouvelle colonne `spell_type`
- **Nouveaux types enum** `combat_status_enum`, `spell_type_enum`

---

## Étape 1 — Boucle de combat complète

C'est le coeur du jeu. Actuellement `battle_service.start_battle()` (`backend/app/services/battle_service.py:61`) ne fait qu'**exécuter un seul sort** et retourne le résultat. Il n'y a ni boucle de tours, ni cooldowns, ni initiative, ni passifs.

### 1a. Refactorer `start_battle()` en boucle tour par tour

**Fichier :** `backend/app/services/battle_service.py`

Le flow cible (d'après le cahier des charges et l'UML) :

```
1. Créer Battle (déjà fait ligne 108)
2. Déterminer l'initiative : qui joue en premier (basé sur SPEED)
3. Boucle while:
   a. Tour du joueur:
      - Choisir un sort disponible (CD = 0, echo suffisant si ultimate)
      - Vérifier le cooldown dans Entity.cds[spell_code]
      - Exécuter run_effects(battle, src, tgt, spell.effects)
      - Mettre le cooldown : src.cds[spell_code] = spell.cooldown_turns
      - Exécuter les passifs on_hit de l'arme (item.passives où trigger == "on_hit")
      - Gain d'Echo : src.gauges["echo"] += 10 (attaque basique) ou 5 (skill)
      - end_turn(battle, src) — ticks des statuts + décrémente CDs
   b. Vérifier si tgt.stats.HP <= 0 → victoire
   c. Tour de l'adversaire (même logique inversée)
   d. Vérifier si src.stats.HP <= 0 → défaite
   e. battle.turn += 1
4. Si max_turns atteint → draw
5. Retourner résultat complet
```

**Points d'attention :**
- Les passifs sont dans `item["passives"]` (voir `couperet_noir.json:8-26`). Il faut itérer dessus et `run_effects()` ceux avec `trigger == "on_hit"` après chaque attaque.
- `status_engine.end_turn()` (`backend/app/engine/status_engine.py:4`) est déjà prêt — il tick les statuts et décrémente les CDs. Il est juste jamais appelé pour l'instant.
- Le `statuses.json` est maintenant chargé dans `Battle.status_defs` (ligne 108) donc `end_turn()` va fonctionner.

### 1b. Initiative (qui joue en premier)

Simple : comparer `src.stats.SPEED` et `tgt.stats.SPEED`. Le plus rapide joue en premier. En cas d'égalité, le joueur (attaquant) joue en premier.

### 1c. Cooldowns

**Avant** de lancer un sort, vérifier :
```python
if src.cds.get(spell_code, 0) > 0:
    # sort en cooldown, choisir un autre
```

**Après** le lancement :
```python
src.cds[spell_code] = spell["cooldown_turns"]
```

Les CDs sont décrémentés par `status_engine.end_turn()` lignes 13-15.

### 1d. Echo system

D'après le cahier des charges :
- Attaque basique → +10 echo
- Sort (SKILL) → +5 echo
- Ultimates coûtent de l'echo : `spell.echo_cost` (dans les JSON)
- Echo max = 100

```python
# Après chaque sort
if spell_type == "ultimate":
    src.gauges["echo"] -= spell.get("echo_cost", 0)
else:
    src.gauges["echo"] = min(100, src.gauges.get("echo", 0) + (10 if spell_type == "basic" else 5))
```

Le `build_gauge` opcode existe déjà et peut aussi être utilisé via les effets JSON.

### 1e. Choix du sort (IA monstre)

Pour le joueur, l'API doit permettre de **choisir** le sort à chaque tour (via endpoint). Pour le monstre, il faut une IA basique :
- Itérer sur `monster.abilities` (JSON)
- Choisir la première ability dont le `cooldown` est disponible, par priorité
- Le champ `ai_behavior` sur Monster pourrait influer plus tard (agressif, défensif...)

---

## Étape 2 — Système d'équipement

**Fichiers principaux :**
- `backend/app/services/inventory_service.py` — `equip_item()` ligne 107 et `unequip_item()` ligne 130 sont des TODO
- `backend/app/models/loadout.py` — le modèle existe avec les 7 slots
- `backend/app/repositories/` — il faudra un `loadout.py` repository

### 2a. Créer `repositories/loadout.py`

Fonctions CRUD :
- `get_by_player_id(db, player_id)` → `PlayerEquipmentLoadout` ou None
- `create(db, player_id)` → crée un loadout vide
- `update_slot(db, player_id, slot_name, item_id)` → met à jour un slot

### 2b. Compléter `equip_item()`

Dans `inventory_service.py:107` :
1. Charger le JSON de l'item (`item_repo.load_item`)
2. Déterminer le slot depuis `item_data["category"]` — mapper "Offensif" → `weapon_primary`, etc. (il faudra peut-être ajouter un champ `slot` dans les JSON d'items)
3. Charger ou créer le `PlayerEquipmentLoadout` du joueur
4. Vérifier si le slot est déjà occupé → si oui, déséquiper l'ancien d'abord
5. Mettre `loadout.weapon_primary_id = item_uid` (selon le slot)
6. Sauvegarder

### 2c. `get_total_stats()`

Nouvelle fonction dans `battle_service.py` ou un `equipment_service.py` :
1. Charger les stats de base du Player
2. Charger le loadout du joueur
3. Pour chaque slot non-null, charger le JSON de l'item et additionner ses stats bonus
4. Retourner le `Stats` total

Ceci sera utilisé par `player_to_entity()` pour que les stats de combat incluent les bonus d'équipement.

### 2d. Ajouter `slot` dans les JSON d'items

Actuellement `couperet_noir.json` a `"category": "Offensif"` mais pas de champ `slot`. Il faut soit :
- Ajouter `"slot": "weapon_primary"` dans chaque JSON
- Soit mapper catégorie → slot dans le code

---

## Étape 3 — PvE monstres

**Fichiers :**
- Créer `backend/app/api/routes/monsters.py` — CRUD routes
- Créer `backend/app/repositories/monster.py` — CRUD fonctions
- Créer `backend/app/schemas/monster.py` — Pydantic schemas
- Modifier `backend/app/services/battle_service.py` — ajouter `start_pve_battle(db, player_id, monster_id, spell_code)`

### 3a. Routes `/monsters`

```
GET    /monsters              → liste tous les monstres
GET    /monsters/{monster_id} → détail d'un monstre
POST   /monsters              → créer (admin/seed)
```

Enregistrer dans `main.py` avec `app.include_router(monsters_router, prefix="/monsters", tags=["monsters"])`.

### 3b. `start_pve_battle()`

Même flow que `start_battle()` sauf :
- La cible est un `Monster` pas un `Player`
- Utiliser `monster_to_entity()` (déjà prêt, `battle_service.py:38`)
- L'adversaire utilise `monster.abilities` au lieu de sorts d'item
- Après victoire : distribuer XP + gold (random entre `reward_gold_min` et `reward_gold_max`)
- Mettre le endpoint dans `backend/app/api/routes/battle.py`

### 3c. Seed data

Créer 2-3 monstres dans la DB ou dans un script seed :
- Gobelin (level 1, facile)
- Dragon (level 10, boss)
- Avec des abilities JSON

---

## Étape 4 — Persistance du combat

Actuellement le combat vit en mémoire et meurt à la fin de la requête HTTP. Pour supporter les combats tour par tour (le joueur choisit son sort à chaque tour via l'API) :

**Fichiers :**
- `backend/app/models/combat_session.py` — existe déjà
- `backend/app/models/combat_log.py` — existe déjà
- Créer `backend/app/repositories/combat.py`
- Modifier `backend/app/services/battle_service.py`
- Modifier `backend/app/api/routes/battle.py`

### 4a. Nouveau flow API

```
POST /combat/start       → crée une CombatSession, retourne session_id + état initial
POST /combat/{id}/action → jouer un tour (spell_code), exécute le tour joueur + monstre, retourne nouvel état
GET  /combat/{id}/state  → état actuel du combat
```

### 4b. Sérialisation Battle ↔ CombatSession

Il faut pouvoir :
1. **Charger** : créer un `Battle` depuis une `CombatSession` (restaurer l'état)
2. **Sauvegarder** : écrire un `Battle` dans une `CombatSession` (persister l'état)

Les champs JSON (`player_statuses`, `player_gauges`, `opponent_statuses`) dans `CombatSession` servent exactement à ça. Les `Entity.statuses` et `Entity.gauges` sont déjà des dicts sérialisables en JSON.

### 4c. CombatLog

À chaque action significative, créer un `CombatLog` en DB au lieu de (ou en plus de) `battle.log.append(str)`. Les champs `turn`, `actor`, `action_type`, `spell_code`, `damage_dealt`, `was_critical`, `echo_gained` permettent d'avoir des logs requêtables.

---

## Étape 5 — Fonctionnalités secondaires (post-MVP)

Par ordre de priorité selon le cahier des charges :

| Feature | Modèle existant ? | Ce qu'il faut créer |
|---|---|---|
| **Auth Twitch OAuth2** | Non | Middleware JWT, endpoint de validation token, dépendances déjà dans requirements.txt (python-jose, passlib) |
| **Quests** | `Quest` model + schemas OK | `repositories/quest.py`, `services/quest_service.py`, `api/routes/quests.py` |
| **Leaderboards** | Non | Model `LeaderboardEntry`, repo, route GET `/leaderboards/{type}` |
| **Achievements** | Non | Models `Achievement` + `PlayerAchievement`, service de tracking |
| **WebSocket combat** | Dépendances socket.io OK | Adapter le flow combat pour émettre des événements WS au lieu de HTTP polling |
| **Donjons** | Non | Models `Dungeon`, `DungeonMonsterSequence`, `PlayerDungeonProgress` |
| **Shop** | `PlayerShop` (vide) | Logique de génération d'items, refresh, achat |

---

## Résumé visuel

```
Étape 0: Migration Alembic (nouvelles tables en DB)
    │
    ▼
Étape 1: Boucle de combat  ← GROS MORCEAU
    │   1a. Boucle while tour par tour
    │   1b. Initiative (SPEED)
    │   1c. Cooldowns
    │   1d. Echo system
    │   1e. Passifs on_hit
    │
    ▼
Étape 2: Équipement
    │   2a. Repository loadout
    │   2b. equip/unequip complet
    │   2c. get_total_stats()
    │
    ▼
Étape 3: PvE monstres
    │   3a. Routes + repo + schemas monsters
    │   3b. start_pve_battle()
    │   3c. Seed data (2-3 monstres)
    │
    ▼
Étape 4: Persistance combat (tour par tour via API)
    │   4a. Nouveaux endpoints /combat/*
    │   4b. Sérialisation Battle ↔ CombatSession
    │   4c. CombatLog en DB
    │
    ▼
Étape 5: Auth, Quests, Leaderboards, WebSocket...
```
