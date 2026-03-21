from pydantic import BaseModel
from typing import Any, Dict, Optional


class InventoryCreate(BaseModel):
    player_id: int
    item_id: str
    quantity: Optional[int] = 1


class InventoryRead(BaseModel):
    inventory_id: int
    player_id: int
    item_id: str
    quantity: int
    equipped_slot: Optional[str] = None
    item_level: int = 1
    item_xp: int = 0
    item_details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    player_id: Optional[int] = None
    item_id: Optional[str] = None
    quantity: Optional[int] = None

    class Config:
        from_attributes = True


# Slot → item détaillé (None si slot vide)
LoadoutRead = Dict[str, Optional[Dict[str, Any]]]


class AssembleRequest(BaseModel):
    player_id: int
    item_id: str
