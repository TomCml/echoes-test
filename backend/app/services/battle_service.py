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
            DEF=player.armor
        )
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
    
    Args:
        db: Session SQLAlchemy
        player_id: ID du joueur attaquant
        target_id: ID de la cible
        item_id: ID de l'item à utiliser
        spell_code: Code du sort à lancer
    
    Returns:
        Dict avec les résultats du combat
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
    
    # 5. Create battle and run effects
    battle = Battle(a=src, b=tgt)
    effects_list = spell.get("effects", [])
    run_effects(battle, src, tgt, effects_list)
    
    # 6. Return results
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
