from fastapi import APIRouter, HTTPException
from app.repositories.item import get_by_id
from app.schemas.item import Item

router = APIRouter()

@router.get("/{item_id}", response_model=Item)
def get_item(item_id: str):
    data = get_by_id(item_id)
    if not data:
        raise HTTPException(404, "Item not found")
    return data
