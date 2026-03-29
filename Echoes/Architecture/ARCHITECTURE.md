# Echoes — Refactoring Combat System (v2 — Rareté)

## Arborescence

```
backend/
├── config/
│   ├── __init__.py
│   └── game_balance.py            ← Tâche 0 : constantes + RarityConfig (★ multipliers)
│
├── core/
│   ├── engine.py                  ← Moteur opcode (events structurés)
│   ├── events.py                  ← Tâche 2 : 14 types d'événements JSON
│   ├── status_engine.py           ← Ticks de statuts
│   └── effects/
│       ├── __init__.py
│       ├── base.py
│       ├── damage.py
│       ├── apply_status.py
│       ├── bonus_damage_if_target_has_status.py
│       ├── build_gauge.py
│       └── heal.py                ← opcode "heal" (consommables)
│
├── models/
│   ├── domain.py                  ← Entity, Battle, Stats, MonsterData
│   └── inventory.py               ← + colonne `rarity` (1-5)
│
├── schemas/
│   ├── battle.py                  ← Actions (TurnAction, ActionCostValidator)
│   └── inventory.py               ← + champ `rarity`
│
├── services/
│   ├── battle_orchestrator_service.py  ← Load DB → Engine → Save (charge rareté depuis DB)
│   ├── stats_calculation_service.py    ← EquippedItem(template, rarity) → stats × mult★
│   ├── monster_ai_service.py           ← IA monstre
│   ├── inventory_service.py            ← Stack par (item_id, rarity) + consume + add
│   ├── item_registry.py               ← NOUVEAU : catalogue items, filter_by_rarity()
│   └── loot_service.py                ← Drops avec plage ★ + gacha 2 étapes
│
└── routes/
    └── battle.py                  ← POST /start + POST /{id}/turn
```

## Système de Rareté (★)

### Principe
Chaque item dans l'inventaire est une **instance** avec une rareté (1★ à 5★).
Le même Item Template JSON peut exister à différentes raretés.

### Multiplicateurs de Stats (RarityConfig)
```
1★ → ×1.00  (base)
2★ → ×1.15
3★ → ×1.35
4★ → ×1.60
5★ → ×2.00
```

Les stats du template JSON sont multipliées par ce facteur quand l'item est équipé.
Configurable via `ECHOES_RARITY_STAR_N_MULT`.

### Éligibilité par rareté
Chaque Item Template JSON déclare optionnellement :
```json
{
  "id": "couperet_noir",
  "min_rarity": 3,
  "max_rarity": 5,
  "stats": { "ad": 25, "armor": 10 }
}
```
Un item avec `min_rarity: 3` ne peut pas être instancié en 1★ ou 2★.

### Inventaire DB
```sql
inventories (
  inventory_id SERIAL PRIMARY KEY,
  player_id    INT REFERENCES players,
  item_id      VARCHAR(100),       -- référence au JSON template
  quantity     INT DEFAULT 1,
  rarity       INT DEFAULT 1       -- 1★ à 5★
)
```
Les items stackent par `(player_id, item_id, rarity)`.
Un joueur peut avoir 3× "potion_hp" à 1★ ET 1× "potion_hp" à 3★.

### Pipeline StatsCalculationService
```
Pour chaque EquippedItem(template, rarity=4) :
  1. Lire stats template : AD=25
  2. Multiplier : 25 × 1.60 (4★) = 40
  3. Sommer aux bonus totaux
```

## Système de Loot (v2)

### Drops d'items (mobs/boss)
Table de drops du monstre (dans `metadata_props.drop_table`) :
```json
{
  "item_id": "couperet_noir",
  "base_rate": 0.03,
  "quantity": 1,
  "min_rarity": 3,
  "max_rarity": 5
}
```

Pipeline :
1. `Taux_Final = base_rate × mult_donjon + extra_drop_rate`
2. Roll : `random() < Taux_Final` → drop réussi
3. **Roll rareté** dans `[min_rarity, max_rarity]` avec poids pondérés :
   ```
   1★ → poids 40
   2★ → poids 30
   3★ → poids 18
   4★ → poids 9
   5★ → poids 3
   ```
4. Instancier `DroppedItem(item_id, rarity, quantity)`

### Coffres — Gacha en 2 étapes

**Étape 1 — Roll Rareté :**
```
T1 (1★) : 50.0%
T2 (2★) : 28.0%
T3 (3★) : 15.4%
T4 (4★) :  6.0%
T5 (5★) :  0.6%
```

**Étape 2 — Roll Item :**
1. `ItemRegistry.filter_by_rarity(rarity)` → items avec `min_rarity ≤ R ≤ max_rarity`
2. Exclure les consommables et quest_items
3. `random.choice(eligible)` → item sélectionné
4. Instancier `DroppedItem(item_id, rarity=R, quantity=1)`
5. Fallback : si aucun item éligible à R★, descendre à R-1, R-2, etc.

### Distribution en DB
```python
inventory_service.add_item(player_id, item_id, quantity=1, rarity=4)
# → Crée ou stack dans inventories WHERE item_id=X AND rarity=4
```

## Flow complet

```
POST /battle/start { player_id, monster_id, equipped_item_ids: ["couperet_noir"] }
  │
  ├─ DB: Inventory WHERE player_id=1 AND item_id="couperet_noir"
  │     → rarity = 4
  │
  ├─ StatsCalculationService.compute_player_stats(
  │     equipped_items=[EquippedItem(template=couperet_json, rarity=4)]
  │   )
  │   → AD du template × 1.60 (4★ mult)
  │
  └─ BattleResult { events: [BATTLE_START], player_hp: 500, ... }

POST /battle/{id}/turn { action: CAST_SPELL, spell_code: "coup_peret" }
  │
  ├─ run_effects() → events [SPELL_CAST, DAMAGE]
  ├─ Monster AI → BASIC_ATTACK → events [DAMAGE]
  ├─ end_turn() → status ticks
  │
  └─ Si monstre mort :
       ├─ LootService.generate_loot()
       │   ├─ XP : 100 × (1 - penalty) = 90
       │   ├─ Gold : 150 × (1 + 0.07 × 12) = 276
       │   ├─ Drops : roll 3% → réussi → roll rarity [3,5] → 4★
       │   └─ Chest : roll T3 (15.4%) → filter items éligibles 3★ → "épée_lumière"
       │
       ├─ _distribute_loot()
       │   ├─ player.experience += 90
       │   ├─ player.gold += 276
       │   ├─ inventory.add_item("couperet_noir", qty=1, rarity=4)
       │   └─ inventory.add_item("épée_lumière", qty=1, rarity=3)
       │
       └─ BattleResult { events: [..., BATTLE_END_LOOT], loot: {...} }
```
