"""
Inventory Repository - Fonctions d'accès DB pour l'inventaire.
Recyclé depuis controllers/inventory.py
"""
import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate

logger = logging.getLogger(__name__)


def get_by_id(db: Session, inventory_id: int) -> Optional[Inventory]:
    """Récupère un inventaire par son ID."""
    return db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()


def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Inventory]:
    """Récupère tous les inventaires avec pagination."""
    return db.query(Inventory).offset(skip).limit(limit).all()


def get_by_player(db: Session, player_id: int) -> List[Inventory]:
    """Récupère l'inventaire d'un joueur."""
    return db.query(Inventory).filter(Inventory.player_id == player_id).all()


def create(db: Session, payload: InventoryCreate) -> Inventory:
    """Crée une nouvelle entrée d'inventaire."""
    inv = Inventory(
        player_id=payload.player_id,
        item_id=payload.item_id,
        quantity=payload.quantity or 1
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    logger.debug(f"Inventory created: {inv.inventory_id}")
    return inv


def update(db: Session, inventory_id: int, payload: InventoryUpdate) -> Optional[Inventory]:
    """Met à jour une entrée d'inventaire."""
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


def delete(db: Session, inventory_id: int) -> bool:
    """Supprime une entrée d'inventaire."""
    inv = db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()
    if not inv:
        return False
    db.delete(inv)
    db.commit()
    return True
