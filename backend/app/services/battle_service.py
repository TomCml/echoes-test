"""
Battle Service - Orchestration des combats.
Utilise le moteur de combat (POO) avec les repositories (fonctions).
"""
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.engine.domain import Battle, Entity, Stats
from app.engine.combat import run_effects
# Import effects to register opcodes
from app.engine import effects  # noqa: F401
from app.repositories import player as player_repo
from app.repositories import item as item_repo

logger = logging.getLogger(__name__)


def player_to_entity(player) -> Entity:
    """Convertit un Player SQLAlchemy en Entity du moteur."""
    return Entity(
        id=str(player.player_id),
        name=player.username,
        stats=Stats(
            MAX_HP=player.health_points,
            HP=player.health_points,
            AD=player.attack_damage,
            AP=player.ability_power or 0,
            ARMOR=player.armor or 0,
            MR=player.magic_resistance or 0,
            SPEED=player.speed or 0,
            CRIT_CHANCE=(player.crit_chance or 0) / 100.0,
            CRIT_DAMAGE=1.5,
        )
    )


def monster_to_entity(monster) -> Entity:
    """Convertit un Monster SQLAlchemy en Entity du moteur."""
    level_bonus_hp = int((monster.scaling_hp or 0) * (monster.level - 1))
    level_bonus_ad = int((monster.scaling_ad or 0) * (monster.level - 1))
    level_bonus_armor = int((monster.scaling_armor or 0) * (monster.level - 1))

    hp = monster.hp_max + level_bonus_hp
    return Entity(
        id=f"monster_{monster.monster_id}",
        name=monster.name,
        stats=Stats(
            MAX_HP=hp,
            HP=hp,
            AD=monster.attack_damage + level_bonus_ad,
            AP=monster.ability_power or 0,
            ARMOR=(monster.armor or 0) + level_bonus_armor,
            MR=monster.magic_resistance or 0,
            SPEED=monster.speed or 0,
        ),
        tags={"boss"} if monster.is_boss else set(),
    )


def start_battle(
    db: Session,
    player_id: int,
    target_id: int,
    item_id: str,
    spell_code: str
) -> Dict[str, Any]:
    """
    Démarre un combat entre deux joueurs.
    """
    # 1. Load players from DB
    player = player_repo.get_by_id(db, player_id)
    if not player:
        return {"error": f"Player {player_id} not found"}

    target = player_repo.get_by_id(db, target_id)
    if not target:
        return {"error": f"Target {target_id} not found"}

    # 2. Load item JSON
    item = item_repo.load_item(item_id)
    if not item:
        return {"error": f"Item {item_id} not found"}

    # 3. Find spell
    spell = None
    for s in item.get("spells", []):
        if s.get("code") == spell_code:
            spell = s
            break

    if not spell:
        return {"error": f"Spell '{spell_code}' not found in item"}

    # 4. Convert to engine entities
    src = player_to_entity(player)
    tgt = player_to_entity(target)

    # 5. Load status definitions
    import json
    from pathlib import Path
    statuses_path = Path("./data/statuses.json")
    status_defs = {}
    if statuses_path.exists():
        status_defs = json.loads(statuses_path.read_text(encoding="utf-8"))

    # 6. Create battle and run effects
    battle = Battle(a=src, b=tgt, status_defs=status_defs)
    effects_list = spell.get("effects", [])
    run_effects(battle, src, tgt, effects_list)

    # 7. Return results
    return {
        "success": True,
        "attacker": src.name,
        "target": tgt.name,
        "spell_used": spell_code,
        "target_hp_remaining": tgt.stats.HP,
        "target_hp_max": tgt.stats.MAX_HP,
        "log": battle.log
    }


def simulate_item_effect(item_id: str) -> Optional[Dict[str, Any]]:
    """Simule les effets d'un item (WIP)."""
    item = item_repo.load_item(item_id)
    if not item:
        return None
    return {"item": item}
