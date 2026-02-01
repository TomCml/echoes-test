from pydantic import BaseModel
from typing import Optional

class InventoryCreate(BaseModel):
    player_id: int
    item_id: str  # Référence au fichier JSON de l'item
    quantity: Optional[int] = 1

class InventoryRead(BaseModel):
    inventory_id: int
    player_id: int
    item_id: str
    quantity: int

    class Config:
        from_attributes = True

class InventoryUpdate(BaseModel):
    player_id: Optional[int] = None
    item_id: Optional[str] = None
    quantity: Optional[int] = None

    class Config:
        from_attributes = True