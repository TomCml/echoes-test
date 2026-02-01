"""
Items Routes - Endpoints pour les items.
"""
from fastapi import APIRouter, HTTPException

from app.repositories import item as item_repo
from app.schemas.item import Item

router = APIRouter()


@router.get("/{item_id}", response_model=Item)
def get_item(item_id: str):
    """Get an item by ID from JSON files."""
    data = item_repo.load_item(item_id)
    if not data:
        raise HTTPException(404, "Item not found")
    return data


@router.get("/")
def list_items():
    """List all available item IDs."""
    return {"items": item_repo.list_items()}
