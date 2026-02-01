"""
Item Repository - Fonctions de chargement des items JSON.
Recyclé depuis controllers/items.py
"""
import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
ITEMS_DIR = DATA_DIR / "items"


def load_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Charge un item depuis les fichiers JSON."""
    path = ITEMS_DIR / f"{item_id}.json"
    logger.debug(f"Loading item from: {path}")
    if not path.exists():
        logger.warning(f"Item not found: {item_id}")
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_items() -> list[str]:
    """Liste tous les IDs d'items disponibles."""
    if not ITEMS_DIR.exists():
        return []
    return [f.stem for f in ITEMS_DIR.glob("*.json")]
