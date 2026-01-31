from fastapi import APIRouter, HTTPException
from controllers.items import load_item
from schemas.item import Item

router = APIRouter()

@router.get("/{item_id}", response_model=Item)
def get_item(item_id: str):
    data = load_item(item_id)
    if not data:
        raise HTTPException(404, "Item not found")
    return data
