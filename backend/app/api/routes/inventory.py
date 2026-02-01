from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import inventory_service

router = APIRouter()


@router.post("/equip/{item_uid}")
def equip(item_uid: str, player_id: int, db: Session = Depends(get_db)):
    result = inventory_service.equip_item(db, player_id, item_uid)
    if "error" in result:
        raise HTTPException(status_code=result.get("status", 400), detail=result["error"])
    return result


@router.post("/unequip/{item_uid}")
def unequip(item_uid: str, player_id: int, db: Session = Depends(get_db)):
    result = inventory_service.unequip_item(db, player_id, item_uid)
    if "error" in result:
        raise HTTPException(status_code=result.get("status", 400), detail=result["error"])
    return result
