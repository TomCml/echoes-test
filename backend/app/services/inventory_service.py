"""
Inventory Service - Logique métier pour l'inventaire.
Utilise les repositories pour l'accès DB.
"""
import logging
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from app.repositories import inventory as inventory_repo
from app.repositories import item as item_repo
from app.repositories import player as player_repo
from app.models.inventory import Inventory

logger = logging.getLogger(__name__)

# Slots valides par type d'item
_SLOT_RULES: Dict[str, List[str]] = {
    "WEAPON": ["weapon_1", "weapon_2"],
    "ECHO": ["echo_1", "echo_2"],
    "HEAD": ["head"],
    "ARMOR": ["armor"],
    "ARTIFACT": ["artifact"],
    "BLESSING": ["blessing"],
    "CONSUMABLE": ["consumable"],
}

ALL_SLOTS = ["weapon_1", "weapon_2", "echo_1", "echo_2", "head", "armor", "artifact", "blessing", "consumable"]


def _validate_slot(item_data: Dict[str, Any], slot: str) -> Optional[str]:
    """Retourne un message d'erreur si le slot est invalide pour cet item, None sinon."""
    item_type = item_data.get("type", "").upper()
    allowed = _SLOT_RULES.get(item_type)
    if allowed is None:
        return f"Type d'item inconnu : '{item_type}'"
    if slot not in allowed:
        return f"L'item de type '{item_type}' ne peut pas aller dans le slot '{slot}'. Slots valides : {allowed}"
    return None


def add_item_to_player(
    db: Session,
    player_id: int,
    item_id: str,
    quantity: int = 1,
) -> Optional[Inventory]:
    """Ajoute un item à l'inventaire d'un joueur, en gérant le stacking."""
    player = player_repo.get_by_id(db, player_id)
    if not player:
        logger.warning(f"Player {player_id} not found")
        return None

    item = item_repo.load_item(item_id)
    if not item:
        logger.warning(f"Item {item_id} not found in data files")
        return None

    return inventory_repo.add_item(db, player_id, item_id, quantity)


def remove_item_from_player(
    db: Session,
    player_id: int,
    item_id: str,
    quantity: int = 1,
) -> bool:
    """Retire un item de l'inventaire d'un joueur."""
    return inventory_repo.remove_item(db, player_id, item_id, quantity)


def get_player_inventory_with_details(db: Session, player_id: int) -> List[Dict[str, Any]]:
    """Récupère l'inventaire du joueur avec les détails des items."""
    inventory = inventory_repo.get_by_player(db, player_id)
    result = []
    for inv in inventory:
        item_data = item_repo.load_item(inv.item_id)
        result.append({
            "inventory_id": inv.inventory_id,
            "item_id": inv.item_id,
            "quantity": inv.quantity,
            "equipped_slot": inv.equipped_slot,
            "item_level": inv.item_level,
            "item_xp": inv.item_xp,
            "item_details": item_data,
        })
    return result


def get_player_loadout(db: Session, player_id: int) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Retourne le loadout complet du joueur sous forme de dict slot → item détaillé.
    Les slots vides sont à None.
    """
    equipped = inventory_repo.get_all_equipped(db, player_id)
    equipped_by_slot = {inv.equipped_slot: inv for inv in equipped}

    loadout: Dict[str, Optional[Dict[str, Any]]] = {}
    for slot in ALL_SLOTS:
        inv = equipped_by_slot.get(slot)
        if inv is None:
            loadout[slot] = None
        else:
            item_data = item_repo.load_item(inv.item_id)
            loadout[slot] = {
                "inventory_id": inv.inventory_id,
                "item_id": inv.item_id,
                "item_level": inv.item_level,
                "item_xp": inv.item_xp,
                "item_details": item_data,
            }
    return loadout


def equip_item_to_slot(
    db: Session,
    inventory_id: int,
    slot: str,
) -> Dict[str, Any]:
    """
    Équipe un item sur un slot, avec validation du type.
    Retourne {"success": True, "equipped_slot": slot} ou {"error": "..."}
    """
    inv = inventory_repo.get_by_id(db, inventory_id)
    if not inv:
        return {"error": "Inventory item not found"}

    item_data = item_repo.load_item(inv.item_id)
    if not item_data:
        return {"error": f"Item data not found for '{inv.item_id}'"}

    error = _validate_slot(item_data, slot)
    if error:
        return {"error": error}

    equipped = inventory_repo.equip_item(db, inventory_id, slot)
    if not equipped:
        return {"error": "Failed to equip item"}

    return {"success": True, "equipped_slot": equipped.equipped_slot}


def assemble_item(db: Session, player_id: int, item_id: str) -> Dict[str, Any]:
    """
    Monte le niveau d'un item en fusionnant des doublons.
    Coût : item_level_actuel + 1 copies non-équipées.
    """
    item_data = item_repo.load_item(item_id)
    if not item_data:
        return {"error": f"Item '{item_id}' introuvable"}

    # Vérifier les copies disponibles avant d'appeler le repo
    entries = inventory_repo.get_by_player(db, player_id)
    unequipped = [e for e in entries if e.item_id == item_id and e.equipped_slot is None]
    if not unequipped:
        return {"error": "Aucune copie non-équipée de cet item"}

    best = max(unequipped, key=lambda e: e.item_level)
    cost = best.item_level + 1
    total_qty = sum(e.quantity for e in unequipped)

    if total_qty < cost:
        return {
            "error": f"Pas assez de copies. Nécessaire : {cost}, disponible : {total_qty}",
            "copies_required": cost,
            "copies_available": total_qty,
        }

    result = inventory_repo.assemble_item(db, player_id, item_id)
    if not result:
        return {"error": "Assemblage échoué"}

    return {
        "success": True,
        "item_id": item_id,
        "new_level": result.item_level,
        "copies_consumed": cost - 1,
    }


def use_consumable(
    db: Session,
    inventory_id: int,
    battle_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Utilise un consommable équipé dans le slot 'consumable'.
    Applique les effets de l'item et retire une charge (quantity -= 1).
    """
    inv = inventory_repo.get_by_id(db, inventory_id)
    if not inv:
        return {"error": "Inventory item not found"}

    if inv.equipped_slot != "consumable":
        return {"error": "Cet item n'est pas équipé dans le slot consommable"}

    item_data = item_repo.load_item(inv.item_id)
    if not item_data:
        return {"error": f"Item data not found for '{inv.item_id}'"}

    if item_data.get("type", "").upper() != "CONSUMABLE":
        return {"error": "Cet item n'est pas un consommable"}

    effects = item_data.get("effects", [])

    # Appliquer les effets en combat si battle_id fourni
    combat_result = None
    if battle_id is not None and effects:
        try:
            from app.services import battle_service
            combat_result = battle_service.apply_consumable_effects(db, battle_id, inv.player_id, effects)
        except Exception as e:
            logger.error(f"Failed to apply consumable effects: {e}")

    # Consommer une charge
    if inv.quantity > 1:
        inv.quantity -= 1
        db.commit()
        db.refresh(inv)
    else:
        inventory_repo.unequip_item(db, inventory_id)
        inventory_repo.remove_item(db, inv.player_id, inv.item_id, 1)

    return {
        "success": True,
        "item_id": inv.item_id,
        "effects_applied": effects,
        "combat_result": combat_result,
    }
