import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from core.database import get_db
from models.player import Player
from controllers.items import load_item
from services.damage_service import DamageService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/simulate/{item_id}")
def simulate(item_id: str) -> Dict[str, Any]:
    """Simulate an item effect (WIP)"""
    item = load_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": item}

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
    # 1. Fetch Player Data
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Attacker (Player) not found")

    target = db.query(Player).filter(Player.player_id == target_id).first()
    if not target:
        # Fallback: créer un joueur vide si pas trouvé
        logger.warning(f"Target {target_id} not found, using empty Player")
        target = Player()

    # 2. Load Item from JSON
    item = load_item(item_id)
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

    # 4. Business Logic (Service)
    result = DamageService.calculate_damage(
        player=player,
        target=target,
        item=item,
        spell=spell,
        crit=crit
    )

    return result
