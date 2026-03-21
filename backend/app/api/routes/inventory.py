from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.repositories import inventory as inventory_repo
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/{player_id}", response_model=List[Dict[str, Any]])
def get_inventory(player_id: int, db: Session = Depends(get_db)):
    """Récupère l'inventaire complet d'un joueur avec les détails des items."""
    return inventory_service.get_player_inventory_with_details(db, player_id)


@router.get("/{player_id}/loadout", response_model=Dict[str, Any])
def get_loadout(player_id: int, db: Session = Depends(get_db)):
    """
    Retourne le loadout équipé du joueur, organisé par slot.
    Les 9 slots : weapon_1, weapon_2, echo_1, echo_2, head, armor, artifact, blessing, consumable.
    Les slots vides sont à null.
    """
    return inventory_service.get_player_loadout(db, player_id)


@router.post("/add")
def add_item_to_inventory(
    player_id: int,
    item_id: str,
    quantity: int = 1,
    db: Session = Depends(get_db),
):
    """Ajoute des objets à l'inventaire d'un joueur."""
    result = inventory_service.add_item_to_player(db, player_id, item_id, quantity)
    if not result:
        raise HTTPException(status_code=400, detail="Item or player not found")
    return {"success": True, "message": f"Added {quantity}x {item_id} to player {player_id}"}


@router.post("/remove")
def remove_item_from_inventory(
    player_id: int,
    item_id: str,
    quantity: int = 1,
    db: Session = Depends(get_db),
):
    """Supprime des objets de l'inventaire."""
    success = inventory_service.remove_item_from_player(db, player_id, item_id, quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Not enough items or item not found")
    return {"success": True, "message": f"Removed {quantity}x {item_id}"}


@router.post("/{inventory_id}/equip")
def equip_inventory_item(inventory_id: int, slot: str, db: Session = Depends(get_db)):
    """
    Équipe un item sur un slot du loadout.
    Valide que le type d'item correspond au slot demandé.
    Slots valides : weapon_1, weapon_2, echo_1, echo_2, head, armor, artifact, blessing, consumable
    """
    result = inventory_service.equip_item_to_slot(db, inventory_id, slot)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{inventory_id}/unequip")
def unequip_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    """Déséquipe un item du loadout et le remet dans l'inventaire général."""
    item = inventory_repo.get_by_id(db, inventory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    inventory_repo.unequip_item(db, inventory_id)
    return {"success": True, "unequipped": True}


@router.post("/assemble")
def assemble_item(player_id: int, item_id: str, db: Session = Depends(get_db)):
    """
    Monte le niveau d'un item par fusion de doublons (gacha).
    Coût : item_level_actuel + 1 copies non-équipées.
    Ex : passer de lvl 1 à lvl 2 coûte 2 copies.
    """
    result = inventory_service.assemble_item(db, player_id, item_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{inventory_id}/use")
def use_consumable(
    inventory_id: int,
    battle_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Utilise un consommable équipé dans le slot 'consumable'.
    Applique les effets et retire une charge.
    Optionnel : fournir battle_id pour appliquer les effets dans le combat en cours.
    """
    result = inventory_service.use_consumable(db, inventory_id, battle_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
