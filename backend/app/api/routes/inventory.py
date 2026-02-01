from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.inventory_service import equip_item, unequip_item
from app.schemas.inventory import InventoryCreate, InventoryUpdate
# Assuming Schema exists, if not, I might need to import from models or use dicts
# backend/schemas/inventory.py existed in file list.

router = APIRouter()

@router.post("/equip/{item_uid}")
def equip(item_uid: str, player_id: int, db: Session = Depends(get_db)):
    try:
        return equip_item(db, player_id, item_uid)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unequip/{item_uid}")
def unequip(item_uid: str, player_id: int, db: Session = Depends(get_db)):
    return unequip_item(db, player_id, item_uid)
