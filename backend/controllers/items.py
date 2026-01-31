import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
ITEMS_DIR = DATA_DIR / "items"

def load_item(item_id: str) -> Optional[Dict[str, Any]]:
    path = ITEMS_DIR / f"{item_id}.json"
    logger.debug(f"Loading item from: {path}")
    if not path.exists():
        logger.warning(f"Item not found: {item_id}")
        return None
    return json.loads(path.read_text(encoding="utf-8"))
