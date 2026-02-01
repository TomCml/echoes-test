from sqlalchemy.orm import Session
from app.repositories import inventory as inventory_repo
from app.repositories import item as item_repo
from app.repositories import player as player_repo
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def equip_item(db: Session, player_id: int, item_uid: str):
    """
    Equip an item for a player.
    Currently, this function verifies ownership and existence.
    The actual 'equip' logic (stat changes or flags) depends on further implementation
    as the current models do not support explicit equipment slots or flags.
    """
    # 1. Verify player exists
    player = player_repo.get_by_id(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # 2. Verify item data exists
    item_data = item_repo.get_by_id(item_uid)
    if not item_data:
        raise HTTPException(status_code=404, detail="Item data not found")

    # 3. Verify player has item in inventory
    # We need to find if the player has an inventory entry with this item_id
    inventories = inventory_repo.get_by_player_id(db, player_id)
    inventory_item = next((inv for inv in inventories if inv.item_id == item_uid), None)

    if not inventory_item:
        raise HTTPException(status_code=400, detail="Player does not possess this item")

    # TODO: Implement actual equip logic (e.g. set is_equipped flag, update player stats, etc.)
    # For now, we just log and return success as a placeholder for the missing logic.
    logger.info(f"Player {player_id} equipped item {item_uid}")
    
    return {"message": f"Item {item_uid} equipped", "item": item_data}

def unequip_item(db: Session, player_id: int, item_uid: str):
    # Placeholder for unequip logic
    logger.info(f"Player {player_id} unequipped item {item_uid}")
    return {"message": f"Item {item_uid} unequipped"}
