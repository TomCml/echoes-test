from sqlalchemy.orm import Session
from app.repositories import player as player_repo
from app.engine.combat import run_effects
from app.engine.status_engine import end_turn
from app.models.domain import Battle, Entity, Stats
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def _player_to_entity(player) -> Entity:
    """Convert DB Player model to Domain Entity."""
    stats = Stats(
        MAX_HP=player.health_points,
        HP=player.health_points,
        AD=player.attack_damage,
        DEF=player.armor
    )
    return Entity(
        id=str(player.player_id),
        name=player.username,
        stats=stats
    )

def start_battle(db: Session, player_id: int, target_id: int) -> Dict[str, Any]:
    """
    Instantiate Battle, play turns, and save result.
    """
    # 1. Fetch participants
    p1_model = player_repo.get_by_id(db, player_id)
    p2_model = player_repo.get_by_id(db, target_id)

    if not p1_model or not p2_model:
        raise ValueError("Player or Target not found")

    # 2. Convert to Domain Entities
    p1 = _player_to_entity(p1_model)
    p2 = _player_to_entity(p2_model)

    # 3. Instantiate Battle
    battle = Battle(a=p1, b=p2)
    
    # 4. Play Battle Loop (Simplified for now - 1 turn or until death)
    
    winner = None
    max_turns = 20
    
    while battle.turn <= max_turns:
        # P1 acts
        dmg_effect = {"opcode": "damage", "params": {"value": 10 + p1.stats.AD}} 
        run_effects(battle, p1, p2, [dmg_effect])
        
        if p2.stats.HP <= 0:
            winner = p1
            break
            
        # B attacks A
        dmg_effect_b = {"opcode": "damage", "params": {"value": 10 + p2.stats.AD}}
        run_effects(battle, p2, p1, [dmg_effect_b])
        
        if p1.stats.HP <= 0:
            winner = p2
            break
        
        # End of turn statuses
        end_turn(battle, p1)
        end_turn(battle, p2)
            
        battle.turn += 1

    # 5. Result
    result = {
        "winner": winner.name if winner else "Draw",
        "log": battle.log,
        "turns": battle.turn
    }
    
    logger.info(f"Battle finished. Winner: {result['winner']}")
    
    # TODO: Save result to DB (History table?)
    
    return result

def process_turn(battle: Battle):
    # Helper if we want step-by-step
    pass
