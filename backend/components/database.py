"""
Layer 1: Component Dimension Database Engine
Parses the nested JSON hardware_library on startup and exposes a clean 
lookup method so the LLM output map strictly to verified physical dimensions.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

HARDWARE_DIR = Path(__file__).parent / "hardware_library"
_COMPONENT_DB = {}

def init_db():
    """Recursively parses all JSON files in the hardware_library/ tree."""
    global _COMPONENT_DB
    _COMPONENT_DB.clear()
    
    if not HARDWARE_DIR.exists():
        logger.warning(f"Hardware library directory not found: {HARDWARE_DIR}")
        return

    for root, _, files in os.walk(HARDWARE_DIR):
        for file in files:
            if file.endswith(".json"):
                path = Path(root) / file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Merge the JSON objects into the global map
                        if isinstance(data, dict):
                            _COMPONENT_DB.update(data)
                except Exception as e:
                    logger.error(f"Failed to load hardware library {file}: {e}")

    logger.info(f"Initialized Component DB with {len(_COMPONENT_DB)} items.")

def lookup(component_key: str) -> dict:
    """Returns the precise physical dimensions for a known item string."""
    item = _COMPONENT_DB.get(component_key)
    if not item:
        logger.error(f"FATAL: Component '{component_key}' missing from dimension DB")
        raise ValueError(f"Component '{component_key}' missing from dimension DB.")
    return item

# Automatically load the DB when the module is imported
init_db()
