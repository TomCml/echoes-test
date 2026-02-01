"""
Inventory Service - Logique métier pour l'inventaire.
Utilise les repositories pour l'accès DB.
"""
import logging
from sqlalchemy.orm import Session
from typing import Optional, List

from app.repositories import inventory as inventory_repo
from app.repositories import item as item_repo
from app.repositories import player as player_repo
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate

logger = logging.getLogger(__name__)


def add_item_to_player(
    db: Session, 
    player_id: int, 
    item_id: str, 
    quantity: int = 1
) -> Optional[Inventory]:
    """
    Ajoute un item à l'inventaire d'un joueur.
    Vérifie que l'item existe et que le joueur existe.
    """
    # Vérifier que le joueur existe
    player = player_repo.get_by_id(db, player_id)
    if not player:
        logger.warning(f"Player {player_id} not found")
        return None
    
    # Vérifier que l'item existe dans les JSON
    item = item_repo.load_item(item_id)
    if not item:
        logger.warning(f"Item {item_id} not found in data files")
        return None
    
    # Vérifier si l'item existe déjà dans l'inventaire
    existing = inventory_repo.get_by_player(db, player_id)
    for inv in existing:
        if inv.item_id == item_id:
            # Incrémenter la quantité
            from app.schemas.inventory import InventoryUpdate
            return inventory_repo.update(
                db, 
                inv.inventory_id, 
                InventoryUpdate(quantity=inv.quantity + quantity)
            )
    
    # Créer une nouvelle entrée
    return inventory_repo.create(
        db, 
        InventoryCreate(player_id=player_id, item_id=item_id, quantity=quantity)
    )


def remove_item_from_player(
    db: Session, 
    player_id: int, 
    item_id: str, 
    quantity: int = 1
) -> bool:
    """
    Retire un item de l'inventaire d'un joueur.
    """
    existing = inventory_repo.get_by_player(db, player_id)
    for inv in existing:
        if inv.item_id == item_id:
            new_qty = inv.quantity - quantity
            if new_qty <= 0:
                return inventory_repo.delete(db, inv.inventory_id)
            else:
                from app.schemas.inventory import InventoryUpdate
                inventory_repo.update(
                    db, 
                    inv.inventory_id, 
                    InventoryUpdate(quantity=new_qty)
                )
                return True
    return False


def get_player_inventory_with_details(
    db: Session, 
    player_id: int
) -> List[dict]:
    """
    Récupère l'inventaire du joueur avec les détails des items.
    """
    inventory = inventory_repo.get_by_player(db, player_id)
    result = []
    
    for inv in inventory:
        item_data = item_repo.load_item(inv.item_id)
        result.append({
            "inventory_id": inv.inventory_id,
            "item_id": inv.item_id,
            "quantity": inv.quantity,
            "item_details": item_data
        })
    
    return result
