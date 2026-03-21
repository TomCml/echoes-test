"""
Inventory Repository - Fonctions d'accès DB pour l'inventaire.
"""
import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate

logger = logging.getLogger(__name__)


def get_by_id(db: Session, inventory_id: int) -> Optional[Inventory]:
    """Récupère une entrée d'inventaire par son ID."""
    return db.query(Inventory).filter(Inventory.inventory_id == inventory_id).first()


def get_by_player(db: Session, player_id: int) -> List[Inventory]:
    """Récupère l'inventaire d'un joueur."""
    return db.query(Inventory).filter(Inventory.player_id == player_id).all()


def get_equipped_item(db: Session, player_id: int, slot: str) -> Optional[Inventory]:
    """Récupère l'objet actuellement équipé dans le slot spécifié."""
    return db.query(Inventory).filter(
        Inventory.player_id == player_id,
        Inventory.equipped_slot == slot
    ).first()


def get_all_equipped(db: Session, player_id: int) -> List[Inventory]:
    """Récupère tous les objets équipés (le loadout) du joueur."""
    return db.query(Inventory).filter(
        Inventory.player_id == player_id,
        Inventory.equipped_slot != None
    ).all()


def add_item(db: Session, player_id: int, item_id: str, quantity: int = 1) -> Inventory:
    """Ajoute un objet à l'inventaire (ou incrémente un stack existant non équipé)."""
    existing = db.query(Inventory).filter(
        Inventory.player_id == player_id,
        Inventory.item_id == item_id,
        Inventory.equipped_slot == None
    ).first()

    if existing:
        existing.quantity += quantity
        db.commit()
        db.refresh(existing)
        return existing
    
    new_item = Inventory(
        player_id=player_id,
        item_id=item_id,
        quantity=quantity,
        equipped_slot=None
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


def remove_item(db: Session, player_id: int, item_id: str, quantity: int = 1) -> bool:
    """Retire une quantité d'un objet (en supprimant d'abord les stacks non équipés)."""
    entries = db.query(Inventory).filter(
        Inventory.player_id == player_id,
        Inventory.item_id == item_id
    ).all()
    
    total_qty = sum(e.quantity for e in entries)
    if total_qty < quantity:
        return False
    
    # Sort: unequipped first
    entries.sort(key=lambda e: (e.equipped_slot is not None, e.quantity))
    
    remaining = quantity
    for entry in entries:
        if remaining <= 0:
            break
        
        if entry.quantity <= remaining:
            remaining -= entry.quantity
            db.delete(entry)
        else:
            entry.quantity -= remaining
            remaining = 0
            
    db.commit()
    return True


def equip_item(db: Session, inventory_id: int, slot: str) -> Optional[Inventory]:
    """Équipe un objet depuis son ID d'inventaire sur un slot donné."""
    item = get_by_id(db, inventory_id)
    if not item:
        return None

    # Retire l'objet actuellement sur ce slot
    current_equipped = get_equipped_item(db, item.player_id, slot)
    if current_equipped:
        current_equipped.equipped_slot = None

    # Si c'est un stack, on détache 1 objet qu'on équipe
    if item.quantity > 1:
        item.quantity -= 1
        equipped_instance = Inventory(
            player_id=item.player_id,
            item_id=item.item_id,
            quantity=1,
            equipped_slot=slot
        )
        db.add(equipped_instance)
        item = equipped_instance
    else:
        item.equipped_slot = slot

    db.commit()
    db.refresh(item)
    return item


def assemble_item(db: Session, player_id: int, item_id: str) -> Optional[Inventory]:
    """
    Monte le niveau d'un item en fusionnant des doublons (gacha).
    Coût : item_level_actuel + 1 copies non-équipées supplémentaires.
    Ex : lvl 1 → lvl 2 coûte 2 copies au total (1 de base + 1 sacrifiée).
    """
    # Toutes les copies non-équipées
    entries = db.query(Inventory).filter(
        Inventory.player_id == player_id,
        Inventory.item_id == item_id,
        Inventory.equipped_slot == None
    ).all()

    if not entries:
        return None

    # Trier par item_level décroissant pour upgrader la meilleure copie
    entries.sort(key=lambda e: e.item_level, reverse=True)
    target = entries[0]
    cost = target.item_level + 1  # copies nécessaires (dont la cible elle-même)

    total_qty = sum(e.quantity for e in entries)
    if total_qty < cost:
        return None  # pas assez de copies

    # Consommer les copies (en commençant par les copies de plus bas niveau)
    entries_to_consume = sorted(entries, key=lambda e: e.item_level)
    remaining_to_consume = cost - 1  # on garde la cible
    for entry in entries_to_consume:
        if entry.inventory_id == target.inventory_id:
            continue
        if remaining_to_consume <= 0:
            break
        if entry.quantity <= remaining_to_consume:
            remaining_to_consume -= entry.quantity
            db.delete(entry)
        else:
            entry.quantity -= remaining_to_consume
            remaining_to_consume = 0

    target.item_level += 1
    db.commit()
    db.refresh(target)
    return target


def unequip_item(db: Session, inventory_id: int) -> Optional[Inventory]:
    """Déséquipe un objet et le remet dans l'inventaire général."""
    item = get_by_id(db, inventory_id)
    if not item or not item.equipped_slot:
        return item

    item.equipped_slot = None
    
    # Fusion avec un stack existant si possible
    existing = db.query(Inventory).filter(
        Inventory.player_id == item.player_id,
        Inventory.item_id == item.item_id,
        Inventory.equipped_slot == None,
        Inventory.inventory_id != item.inventory_id
    ).first()
    
    if existing:
        existing.quantity += item.quantity
        db.delete(item)
        db.commit()
        db.refresh(existing)
        return existing
        
    db.commit()
    db.refresh(item)
    return item
