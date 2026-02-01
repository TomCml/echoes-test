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
    MAX_HP, HP, AD, DEF

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
| `damage.py` | `damage` | Dégâts avec formule, variance, crit |
| `apply_status.py` | `apply_status` | Applique un statut avec chance de résistance |
| `bonus_damage_if_target_has_status.py` | `bonus_damage_if_target_has_status` | Dégâts bonus % AD si la cible a un statut |
| `build_gauge.py` | `build_gauge` | Incrémente une jauge (conditionnel à un statut) |
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
| `equipement.py` | `weapons`, `spells` | Armes avec bonus stats, sorts avec type de dégât/coût/cooldown/effets JSON |
| `monster.py` | `monsters` | Monstres PvE avec stats et récompenses |
| `quest.py` | `quests` | Quêtes avec type (Unique/Repeatable) et catégorie |
| `title.py` | `titles` | Titres de joueur |
| `player_shop.py` | `player_shop` | Shop joueur (structure minimale) |
| `damage_types.py` | *(enum)* | `DamageType`: PHYSICAL, MAGICAL, TRUE, HEALING |

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

## Où continuer le projet

### Priorité 1 — Compléter le système de combat
- [ ] **Battle loop complète** : le `battle_service.start_battle()` actuel ne fait qu'exécuter un seul sort. Il faut implémenter la boucle de combat avec alternance de tours, cooldowns, et choix de sorts. Regarder la version Gemini de `battle_service.py` pour l'inspiration de la boucle while.
- [ ] **Charger `statuses.json`** dans `Battle.status_defs` au démarrage d'un combat pour que `status_engine.end_turn()` puisse résoudre les ticks.
- [ ] **Passives** : implémenter le trigger `on_hit` pour exécuter les passifs d'un item à chaque attaque.
- [ ] **Cooldowns** : intégrer `Entity.cds` dans la logique de sélection de sort.

### Priorité 2 — Système d'équipement
- [ ] **Slots d'équipement** : ajouter un modèle ou un champ sur Player pour tracker les items équipés (arme, armure, accessoire...).
- [ ] **Modifier les stats** : quand un item est équipé, appliquer ses bonus aux stats du joueur.
- [ ] **Compléter `equip_item()` et `unequip_item()`** dans `inventory_service.py`.

### Priorité 3 — Fonctionnalités manquantes
- [ ] **Routes quêtes** : les models/schemas existent mais aucune route ni service.
- [ ] **Routes monstres** : pareil, le modèle Monster existe mais pas d'API.
- [ ] **PvE** : combats contre des monstres (adapter `battle_service` pour accepter un Monster comme cible).
- [ ] **Historique de combat** : sauvegarder les résultats en DB.

### Priorité 4 — Infra et qualité
- [ ] **Alembic migrations** : s'assurer que les migrations sont à jour avec les modèles.
- [ ] **Tests** : aucun test actuellement. Le moteur d'effets est très testable unitairement.
- [ ] **WebSocket** : les dépendances socket.io sont là mais rien n'est implémenté. Pour le combat en temps réel ?
- [ ] **Auth** : les dépendances JWT (python-jose, passlib) sont là mais pas utilisées. Implémenter un vrai système de tokens.

### Fichiers clés à modifier en premier
1. `app/services/battle_service.py` — Boucle de combat complète
2. `app/services/inventory_service.py` — Logique d'équipement
3. `app/engine/effects/` — Ajouter de nouveaux effets
4. `data/items/` — Ajouter de nouveaux items
5. `data/statuses.json` — Ajouter de nouveaux statuts
