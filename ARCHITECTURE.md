# Echoes — Architecture Backend

## Structure globale

```
backend/
├── main.py                          # Point d'entrée FastAPI
├── requirements.txt                 # Dépendances Python
├── dockerfile                       # Container Python 3.12
├── alembic.ini                      # Config migrations DB
├── alembic/                         # Migrations Alembic
│   ├── env.py                       # Env Alembic (avec Infisical)
│   └── versions/                    # Fichiers de migration
├── data/                            # Données statiques (JSON)
│   ├── items/                       # Définitions des items
│   │   └── couperet_noir.json
│   └── statuses.json                # Définitions des statuts
└── app/
    ├── api/routes/                   # Layer 1 — Routes HTTP
    ├── services/                     # Layer 2 — Logique métier
    ├── repositories/                 # Layer 3 — Accès données
    ├── engine/                       # Moteur de combat (POO)
    │   ├── domain.py                # Entités de combat
    │   ├── combat.py                # Registre d'effets + helpers
    │   ├── status_engine.py         # Gestion des statuts par tour
    │   └── effects/                 # Effets modulaires
    ├── models/                       # Modèles SQLAlchemy (DB)
    ├── schemas/                      # Schémas Pydantic (API)
    └── core/                         # Configuration (DB)
```

## Flux de données

```
Client HTTP
    │
    ▼
Routes (app/api/routes/)     ← Validation des entrées, HTTP errors
    │
    ▼
Services (app/services/)     ← Orchestration, logique métier
    │
    ├──► Repositories         ← Accès DB (SQLAlchemy) + chargement JSON
    │
    └──► Engine               ← Moteur de combat (POO, dataclasses)
            │
            ├── domain.py     ← Battle, Entity, Stats
            ├── combat.py     ← run_effects(), registre d'opcodes
            └── effects/      ← Chaque effet dans son fichier
```

---

## Fichier par fichier

### `backend/main.py`
Point d'entrée. Crée l'app FastAPI, configure Infisical SDK pour les secrets, et enregistre les routers :
- `/items` — CRUD items
- `/battle` — Combat et calcul de dégâts
- `/login` — Authentification Twitch
- `/players` — CRUD joueurs
- `/inventory` — Équipement d'items

Endpoint `/health` qui vérifie la connexion à Infisical.

---

### Routes — `app/api/routes/`

#### `battle.py`
| Endpoint | Méthode | Description |
|---|---|---|
| `/battle/simulate/{item_id}` | POST | Simule les effets d'un item (WIP) |
| `/battle/damages-calculation` | GET | Calcul détaillé des dégâts d'un sort (avec crit, armor, MR) |
| `/battle/start` | POST | Lance un combat entre 2 joueurs avec un item/sort spécifique |

Le endpoint `damages-calculation` utilise `damage_service.calculate_damage()` pour un calcul théorique complet (ratios AD/AP, mitigations armor/MR).

Le endpoint `start` utilise `battle_service.start_battle()` qui passe par le moteur de combat (engine).

#### `items.py`
| Endpoint | Méthode | Description |
|---|---|---|
| `/items/{item_id}` | GET | Charge un item depuis les JSON |
| `/items/` | GET | Liste tous les IDs d'items disponibles |

#### `login.py`
| Endpoint | Méthode | Description |
|---|---|---|
| `/login/login` | POST | Login Twitch — crée le joueur si inexistant |

Prend un `PlayerCreate` (twitch_id + username). Si le joueur existe déjà (par twitch_id), le retourne. Sinon, le crée.

#### `players.py`
| Endpoint | Méthode | Description |
|---|---|---|
| `/players/{player_id}` | GET | Récupère un joueur par ID |
| `/players/{player_id}` | PATCH | Met à jour les champs d'un joueur |
| `/players/{player_id}` | DELETE | Supprime un joueur |

#### `inventory.py`
| Endpoint | Méthode | Description |
|---|---|---|
| `/inventory/equip/{item_uid}` | POST | Équipe un item (vérifie possession) |
| `/inventory/unequip/{item_uid}` | POST | Déséquipe un item |

Les deux prennent `player_id` en query param.

---

### Services — `app/services/`

#### `battle_service.py`
Fonctions :
- **`player_to_entity(player)`** — Convertit un `Player` SQLAlchemy en `Entity` du moteur de combat.
- **`start_battle(db, player_id, target_id, item_id, spell_code)`** — Orchestre un combat :
  1. Charge les 2 joueurs depuis la DB
  2. Charge l'item JSON
  3. Trouve le sort dans l'item
  4. Convertit en Entity
  5. Crée un Battle et exécute les effets du sort
  6. Retourne le log + HP restants
- **`simulate_item_effect(item_id)`** — Placeholder, retourne juste les données de l'item.

#### `damage_service.py`
Fonction **`calculate_damage(player, target, item, spell, crit)`** — Calcul théorique complet :
- Extrait les ratios AD/AP/HP/armor/MR/speed depuis les params du sort
- Applique les ratios aux stats du joueur
- Multiplie par crit (x1.5)
- Applique les mitigations armor/MR avec formule exponentielle : `e^(-armor/448.6)`
- Retourne un breakdown détaillé (raw, crit, post-mitigation, final)

#### `inventory_service.py`
Fonctions :
- **`add_item_to_player(db, player_id, item_id, quantity)`** — Ajoute un item à l'inventaire. Si déjà présent, incrémente la quantité.
- **`remove_item_from_player(db, player_id, item_id, quantity)`** — Retire un item. Supprime l'entrée si quantité tombe à 0.
- **`get_player_inventory_with_details(db, player_id)`** — Retourne l'inventaire avec les données JSON de chaque item.
- **`equip_item(db, player_id, item_uid)`** — Vérifie que le joueur possède l'item, puis l'équipe. **TODO: logique de slots + stats.**
- **`unequip_item(db, player_id, item_uid)`** — Placeholder. **TODO: logique de déséquipement.**

---

### Engine — `app/engine/`

C'est le coeur du système de combat. Utilise des **dataclasses** (POO légère) pour les entités.

#### `domain.py` — Entités de combat
```python
@dataclass
class Stats:
    MAX_HP, HP, AD, AP, ARMOR, MR, SPEED, CRIT_CHANCE, CRIT_DAMAGE
    DEF -> property alias de ARMOR

@dataclass
class Entity:
    id, name, stats: Stats
    tags: Set[str]           # Tags de l'entité
    statuses: Dict           # code -> {remaining, stacks}
    gauges: Dict[str, int]   # Jauges custom (echo, rage, etc.)
    cds: Dict[str, int]      # Cooldowns des sorts

@dataclass
class Battle:
    a, b: Entity             # Les 2 combattants
    turn: int                # Tour actuel
    status_defs: Dict        # Définitions des statuts (depuis statuses.json)
    log: List[str]           # Journal de combat
    rng: Random              # RNG seedé (reproductible)

    def other(who) -> Entity # Retourne l'adversaire
```

#### `combat.py` — Registre d'effets
- **`REGISTRY`** — Dict opcode -> fonction d'effet
- **`register(opcode)`** — Décorateur pour enregistrer un effet
- **`run_effects(battle, src, tgt, effects)`** — Exécute une liste d'effets triés par `order`
- **`eval_formula(expr, src, tgt)`** — Évalue une formule string avec les stats en scope (`S_AD`, `T_MAX_HP`, etc.)
- **`apply_damage(battle, target, amount, label)`** — Applique des dégâts, log le résultat
- **`apply_status(battle, target, code, duration, stacks)`** — Applique ou empile un statut

#### `status_engine.py`
- **`end_turn(battle, who)`** — Appelé en fin de tour :
  - Exécute les ticks des statuts actifs (ex: saignement)
  - Décrémente les durées, supprime les statuts expirés
  - Décrémente les cooldowns

#### `effects/` — Effets modulaires
Chaque fichier enregistre un opcode via `@register("opcode")`. L'`__init__.py` importe tous les modules pour déclencher l'enregistrement au démarrage.

| Fichier | Opcode | Description |
|---|---|---|
| `damage.py` | `damage` | Dégâts avec formule, variance, crit (utilise CRIT_CHANCE/CRIT_DAMAGE de l'Entity) |
| `apply_status.py` | `apply_status` | Applique un statut avec chance de résistance |
| `bonus_damage_if_target_has_status.py` | `bonus_damage_if_target_has_status` | Dégâts bonus % AD si la cible a un statut |
| `build_gauge.py` | `build_gauge` | Incrémente une jauge (conditionnel à un statut) |
| `heal.py` | `heal` | Soins via formule, cap à MAX_HP |
| `modify_stat.py` | `modify_stat` | Buff/debuff temporaire d'une stat (AD, ARMOR, etc.) |
| `remove_status.py` | `remove_status` | Retire un statut spécifique de la cible |
| `shield.py` | `shield` | Bouclier absorbant via gauge "shield" (consommé par apply_damage) |
| `base.py` | *(pas d'opcode)* | Helper `percent_bonus_from_ad()` |

**Pour ajouter un nouvel effet :**
1. Créer `effects/mon_effet.py`
2. `@register("mon_opcode")` sur la fonction
3. Ajouter `from . import mon_effet` dans `effects/__init__.py`
4. Utiliser `"opcode": "mon_opcode"` dans les JSON d'items

---

### Models — `app/models/` (SQLAlchemy)

| Fichier | Table | Description |
|---|---|---|
| `player.py` | `players` | Joueur avec toutes les stats RPG (HP, AD, AP, armor, MR, crit, dodge, speed, life steal, spell vamp), progression (level, XP, gold), système Echo, intégration Twitch |
| `inventory.py` | `inventories` | Lien joueur ↔ item (item_id = référence JSON), quantité |
| `equipement.py` | `weapons`, `spells` | Armes avec bonus stats, sorts avec type de dégât/coût/cooldown/effets JSON. Spell a un `spell_type` (BASIC/SKILL/ULTIMATE). |
| `monster.py` | `monsters` | Monstres PvE avec stats complètes (HP, AD, AP, armor, MR, speed), scaling par niveau, abilities JSON, récompenses min/max gold, flag boss |
| `loadout.py` | `player_equipment_loadout` | 7 slots d'équipement (weapon_primary, weapon_secondary, head, armor, artifact, blessing, consumable) — référence des item_id JSON |
| `combat_session.py` | `combat_sessions` | Session de combat persistée (état joueur/adversaire, statuts, jauges, timestamps) |
| `combat_log.py` | `combat_logs` | Logs structurés (turn, actor, spell, damage, crit, echo, type de dégât) |
| `quest.py` | `quests` | Quêtes avec type (Unique/Repeatable) et catégorie |
| `title.py` | `titles` | Titres de joueur |
| `player_shop.py` | `player_shop` | Shop joueur (structure minimale) |
| `damage_types.py` | *(enum)* | `DamageType`: PHYSICAL, MAGICAL, TRUE, MIXED, STASIS, HEALING |
| `enums.py` | *(enums)* | `SpellType`, `EquipmentSlot`, `Rarity`, `CombatStatus`, `TickTrigger` |

---

### Schemas — `app/schemas/` (Pydantic)

| Fichier | Classes | Description |
|---|---|---|
| `player.py` | `LoginRequest`, `PlayerCreate`, `PlayerRead`, `PlayerResponse`, `PlayerUpdate` | Validation API joueur. `PlayerResponse` = alias de `PlayerRead` |
| `inventory.py` | `InventoryCreate`, `InventoryRead`, `InventoryUpdate` | Validation API inventaire |
| `item.py` | `Effect`, `Passive`, `Spell`, `Item` | Validation des données JSON d'items |
| `quest.py` | `QuestType`, `QuestCategory`, `QuestCreate/Read/Update` | Validation API quêtes |
| `title.py` | `TitleCreate/Read/Update` | Validation API titres |

---

### Repositories — `app/repositories/`

| Fichier | Fonctions | Source |
|---|---|---|
| `player.py` | `get_by_id`, `get_by_twitch_id`, `create`, `update`, `delete` | PostgreSQL |
| `inventory.py` | `get_by_id`, `get_all`, `get_by_player`, `create`, `update`, `delete` | PostgreSQL |
| `item.py` | `load_item(id)`, `list_items()` | Fichiers JSON (`data/items/`) |

---

### Data — `data/`

#### `items/couperet_noir.json`
Arme offensive avec tag `armor_pen`. Contient :
- **1 passive** "Écho Lacérant" (on_hit) : bonus 10% AD si la cible a `laceration` + build gauge `echo`
- **3 sorts** :
  - `coup_peret` (CD 3) : `140 + S_AD * 0.90`, can_crit
  - `entaille_profonde` (CD 11) : applique `laceration` 3 tours
  - `execution` (CD 13) : `200 + S_AD * 1.60`, cannot_crit

#### `statuses.json`
Définitions des statuts. Actuellement :
- `laceration` : debuff/bleed, tick on_turn_end = `T_MAX_HP * 0.03` (3% HP max en saignement)

---

## Écarts entre la doc de design et le code actuel

La doc dans `/Echoes/` décrit une architecture cible bien plus complète. Voici les écarts majeurs.

### Modèle de données : Code vs Design

| Concept Design (UML/SQL) | Code actuel | Écart |
|---|---|---|
| `users` + `players` séparés (UUID) | `players` seul (Integer PK, twitch_id direct) | **Pas de table users.** Le player contient directement le twitch_id. Le design prévoit une séparation User/Player avec UUIDs. |
| `item_blueprints` + `weapon_blueprints` + `equipment_blueprints` + `consumable_blueprints` (héritage en DB) | `weapons` + `spells` en DB, items en JSON | **Système hybride.** Les items sont des JSON files, pas des blueprints en DB. Le design prévoit tout en DB avec héritage. |
| `item_instances` (items possédés avec level/XP propre) | `inventories` (player_id + item_id + quantity) | **Pas d'instances levellable.** L'inventaire actuel est un simple compteur, pas d'item_level/item_xp. |
| `player_equipment_loadout` (7 slots nommés) | `PlayerEquipmentLoadout` modèle créé (7 slots, ref item_id JSON) | **FAIT (modèle).** Le service equip/unequip reste à brancher dessus. |
| `combat_sessions` (persisté en DB avec état complet) | `CombatSession` modèle créé | **FAIT (modèle).** Le modèle existe, pas encore branché au service. |
| `combat_logs` (table avec turn, actor, damage, crit, echo) | `CombatLog` modèle créé | **FAIT (modèle).** Le modèle existe, les logs runtime restent des strings. Il faudra brancher la persistance. |
| `combat_spell_cooldowns` (persisté en DB) | `Entity.cds: Dict` (runtime) | **Cooldowns en mémoire** uniquement. Les CDs seront persistés via CombatSession si nécessaire. |
| `monster_blueprints` + `monster_abilities` (stats, scaling, IA, loot) | `monsters` enrichi (AP, armor, MR, speed, scaling, abilities JSON, boss flag, gold min/max) | **FAIT.** Monster a maintenant toutes les stats, le scaling, et les abilities en JSON. |
| `status_definitions` (en DB, avec icon, max_stacks, stackable flag) | `statuses.json` (fichier JSON) | **Statuts en JSON.** Le design les veut en DB. |
| `dungeons` + `dungeon_monster_sequence` + `player_dungeon_progress` | Rien | **Pas de donjons.** |
| `achievements` + `player_achievements` | Rien | **Pas d'achievements.** |
| `quests` + `player_quests` | Modèle Quest existe mais aucune route/service | **Quêtes orphelines.** |
| `leaderboard_entries` | Rien | **Pas de leaderboard.** |
| `loot_tables` + `loot_table_entries` | Rien | **Pas de loot.** |
| `StatsBlock` (MAX_HP, HP, AD, AP, ARMOR, MR, SPEED, CRIT_CHANCE, CRIT_DAMAGE) | `Stats(MAX_HP, HP, AD, AP, ARMOR, MR, SPEED, CRIT_CHANCE, CRIT_DAMAGE)` | **FAIT.** Stats complètes, DEF = alias de ARMOR. |
| `DamageType`: PHYSICAL, MAGIC, TRUE, MIXED, STASIS | `DamageType`: PHYSICAL, MAGICAL, TRUE, MIXED, STASIS, HEALING | **FAIT.** MIXED et STASIS ajoutés, HEALING gardé. |
| `SpellType`: BASIC, SKILL, ULTIMATE | `SpellType` dans `enums.py`, utilisé par `Spell` model | **FAIT.** |
| `EquipmentSlot`: 7 slots | `EquipmentSlot` dans `enums.py`, utilisé par `PlayerEquipmentLoadout` | **FAIT.** |
| `Rarity`: COMMON → LEGENDARY | `Rarity` dans `enums.py` | **FAIT.** Enum défini, pas encore utilisé dans les modèles. |
| Echo system (gain par attaque/sort, coût pour ultimate) | `echo_current/echo_max` sur Player, `build_gauge` opcode existe | **Partiellement là.** Le gauge "echo" existe dans le moteur mais pas la logique de coût/ultimate. |

### Effets : existants vs prévus (UML note)

| Opcode | Implémenté | Prévu dans le design |
|---|---|---|
| `damage` | Oui | Oui |
| `apply_status` | Oui | Oui |
| `build_gauge` | Oui | Oui |
| `bonus_damage_if_target_has_status` | Oui | Oui |
| `heal` | **Oui** | Oui |
| `modify_stat` | **Oui** | Oui |
| `remove_status` | **Oui** | Oui |
| `echo_gain` | Via `build_gauge` (gauge="echo") | Oui (via build_gauge) |
| `shield` | **Oui** (+ absorption dans apply_damage) | Oui |

### Phases du planning backend vs avancement

| Phase | Description | Statut |
|---|---|---|
| Phase 1 | Infrastructure DB (SQLAlchemy + Alembic) | **Fait** |
| Phase 2 | Modèles combat (Player, Monster, Weapon, Spell) | **Partiellement fait** — modèles existent mais pas alignés avec le design |
| Phase 3 | Repository Layer (CRUD) | **Fait** pour player, inventory, item |
| Phase 4 | Schemas Pydantic | **Fait** pour player, inventory, item, quest, title |
| Phase 5 | Services (Echo, Equipment, Damage, Initiative, Combat) | **Partiellement fait** — damage_service et battle_service existent, pas d'initiative/echo service |
| Phase 6 | API Endpoints | **Partiellement fait** — battle, items, login, players, inventory. Manque: monsters, equipment détaillé |
| Phase 7 | Seed Data | **Partiellement fait** — 1 item JSON + 1 status JSON. Manque: monstres, armes starter |
| Phase 8 | Tests combat | **Pas fait** |
| Phase 9+ | WebSocket, Leaderboards, Full Inventory, Shop, Quests, Auth, PubSub, Dungeons | **Pas fait** |

---

## Où continuer le projet

### Décision architecturale à prendre d'abord

Le code actuel utilise un **système hybride** :
- Items = fichiers JSON (blueprints)
- Players/Inventory = DB (SQLAlchemy)
- Combat = runtime (dataclasses en mémoire)

Le design dans `/Echoes/Architecture/` prévoit **tout en DB** (item_blueprints, combat_sessions, status_definitions...).

**Tu dois décider :** rester en hybride JSON+DB (plus simple, plus rapide à itérer sur les items) ou migrer vers le schéma SQL complet du design ? Les deux sont viables pour le MVP.

### ~~Priorité 1 — Aligner le domain engine avec le design~~ FAIT
- [x] Stats enrichi (AP, MR, SPEED, CRIT_CHANCE, CRIT_DAMAGE)
- [x] player_to_entity() mappe toutes les stats + monster_to_entity() ajouté
- [x] DamageType aligné (MIXED, STASIS ajoutés)
- [x] SpellType, EquipmentSlot, Rarity, CombatStatus, TickTrigger ajoutés
- [x] Modèles PlayerEquipmentLoadout, CombatSession, CombatLog créés
- [x] Monster enrichi (stats complètes, scaling, abilities, boss, gold min/max)
- [x] 4 nouveaux effets (heal, modify_stat, remove_status, shield)
- [x] Shield absorbé par apply_damage
- [x] Crit utilise CRIT_CHANCE/CRIT_DAMAGE de l'Entity (plus hardcodé)

### Priorité 1 — Boucle de combat complète
- [ ] **Battle loop** : implémenter la boucle tour par tour dans `battle_service.start_battle()` — alternance joueur/monstre, sélection de sort, cooldowns, initiative (speed)
- [ ] **Charger `statuses.json`** dans `Battle.status_defs` au lancement du combat
- [ ] **Passives on_hit** : exécuter les passifs de l'arme à chaque attaque
- [ ] **Echo system** : gain par attaque basique (10) et par sort (5), coût pour ultimates
- [ ] **Cooldowns** : vérifier `Entity.cds` avant de lancer un sort, set CD après usage

### Priorité 2 — Système d'équipement
- [x] ~~Table `player_equipment_loadout`~~ FAIT (modèle créé)
- [ ] **Compléter `equip_item()` / `unequip_item()`** : valider le slot, mettre à jour le loadout, recalculer les stats
- [ ] **`get_total_stats()`** : agréger stats de base du player + bonus des items équipés

### Priorité 3 — PvE et monstres
- [x] ~~Enrichir le modèle Monster~~ FAIT
- [ ] **Routes `/monsters`** : CRUD + endpoint pour instancier un MonsterEntity
- [ ] **Adapter `battle_service`** : accepter un Monster comme adversaire (pas seulement un Player)
- [ ] **Loot** : après victoire, roller la loot table et distribuer les items

### Priorité 4 — Persistance du combat
- [x] ~~Tables `combat_sessions` et `combat_logs`~~ FAIT (modèles créés)
- [ ] **Brancher la persistance** : sauvegarder/charger CombatSession depuis battle_service
- [ ] **Endpoint `GET /combat/{id}/state`** : récupérer l'état d'un combat en cours

### Priorité 5 — Fonctionnalités secondaires
- [ ] **Quests** : routes + service pour le système de quêtes (modèle déjà là)
- [ ] **Achievements** : nouveau modèle + service
- [ ] **Leaderboards** : nouveau modèle + endpoint
- [ ] **Donjons** : séquence de monstres avec boss final
- [ ] **Auth Twitch OAuth2** : JWT tokens, middleware d'authentification
- [ ] **WebSocket** : combat en temps réel via socket.io

### ~~Nouveaux effets~~ FAIT
- [x] `heal`, `modify_stat`, `remove_status`, `shield` — tous implémentés
- `echo_gain` couvert par `build_gauge` avec `gauge: "echo"`

### Fichiers clés à modifier en premier
1. `app/engine/domain.py` — Enrichir Stats (AP, MR, SPEED, CRIT)
2. `app/services/battle_service.py` — Boucle de combat complète
3. `app/services/inventory_service.py` — Logique d'équipement avec loadout
4. `app/engine/effects/` — Nouveaux opcodes (heal, shield, modify_stat)
5. `app/models/` — Nouveaux modèles (loadout, combat_session) ou enrichir les existants
6. `data/items/` — Ajouter de nouveaux items
7. `data/statuses.json` — Ajouter de nouveaux statuts (burn, freeze, stun...)
