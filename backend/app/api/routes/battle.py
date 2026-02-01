"""
Battle Routes - Endpoints pour le système de combat.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services import damage_service, battle_service
from app.repositories import player as player_repo
from app.repositories import item as item_repo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/simulate/{item_id}")
def simulate(item_id: str) -> Dict[str, Any]:
    """Simulate an item effect (WIP)"""
    result = battle_service.simulate_item_effect(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.get("/damages-calculation")
def get_damages_calculation(
    crit: bool, 
    item_id: str = Query(..., description="ID of the item/weapon (JSON)"),
    spell_code: str = Query(..., description="Code of the spell to use"),
    player_id: int = Query(1, description="ID of the attacker"),
    target_id: int = Query(2, description="ID of the target"),
    db: Session = Depends(get_db)
):
    """Calculate damage for a spell attack"""
    # 1. Fetch Player Data via repository
    player = player_repo.get_by_id(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Attacker (Player) not found")

    target = player_repo.get_by_id(db, target_id)
    if not target:
        # Fallback: créer un joueur vide si pas trouvé
        logger.warning(f"Target {target_id} not found, using empty Player")
        from app.models.player import Player
        target = Player()

    # 2. Load Item from JSON via repository
    item = item_repo.load_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 3. Find the spell in the item
    spell = None
    for s in item.get("spells", []):
        if s.get("code") == spell_code:
            spell = s
            break
    
    if not spell:
        raise HTTPException(status_code=404, detail=f"Spell '{spell_code}' not found in item")

    # 4. Business Logic via service
    result = damage_service.calculate_damage(
        player=player,
        target=target,
        item=item,
        spell=spell,
        crit=crit
    )

    return result


@router.post("/start")
def start_battle_endpoint(
    player_id: int = Query(..., description="ID of the attacker"),
    target_id: int = Query(..., description="ID of the target"),
    item_id: str = Query(..., description="ID of the item/weapon (JSON)"),
    spell_code: str = Query(..., description="Code of the spell to use"),
    db: Session = Depends(get_db)
):
    """Start a battle between two players using the combat engine."""
    result = battle_service.start_battle(db, player_id, target_id, item_id, spell_code)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
