import logging
import json
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
STATUS_PATH = DATA_DIR / "statuses.json"

def load_status_defs() -> Dict[str, Any]:
    logger.debug(f"Loading status definitions from: {STATUS_PATH}")
    with open(STATUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
