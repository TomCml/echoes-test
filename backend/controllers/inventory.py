import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from models.inventory import Inventory
from schemas.inventory import InventoryCreate, InventoryUpdate

logger = logging.getLogger(__name__)

def get_inventory(db: Session, inventory_id: int) -> Optional[Inventory]:
    return db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()

def get_inventories(db: Session, skip: int = 0, limit: int = 100) -> List[Inventory]:
    return db.query(Inventory).offset(skip).limit(limit).all()

def get_inventories_by_player(db: Session, player_id: int) -> List[Inventory]:
    return db.query(Inventory).filter(Inventory.player_id == player_id).all()

def create_inventory(db: Session, payload: InventoryCreate) -> Inventory:
    inv = Inventory(
        player_id=payload.player_id,
        item_id=payload.item_id,  # String reference to JSON item
        quantity=payload.quantity or 1
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    logger.debug(f"Inventory created: {inv.inventory_id}")
    return inv

def update_inventory(db: Session, inventory_id: int, payload: InventoryUpdate) -> Optional[Inventory]:
    inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
    if not inv:
        return None
    updates = payload.model_dump(exclude_unset=True)
    
    for k, v in updates.items():
        if hasattr(inv, k):
            setattr(inv, k, v)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

def delete_inventory(db: Session, inventory_id: int) -> bool:
    inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
    if not inv:
        return False
    db.delete(inv)
    db.commit()
    return True