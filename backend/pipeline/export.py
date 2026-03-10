"""
Gridfinity AI — Export Module

Handles saving generated meshes to disk and returning URLs.
"""

import os
import uuid
import logging

from core.schemas import BinConfig

logger = logging.getLogger(__name__)

# ── Output directory ─────────────────────────────────────────────────────────

GENERATED_DIR = os.path.join(os.path.dirname(__file__), "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


def save_stl(stl_bytes: bytes) -> str:
    """Save STL bytes to disk. Returns the filename."""
    filename = f"{uuid.uuid4().hex[:12]}.stl"
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(stl_bytes)
    logger.info(f"Saved STL: {filepath} ({len(stl_bytes)} bytes)")
    return filename


def save_glb(glb_bytes: bytes) -> str:
    """Save GLB bytes to disk. Returns the filename."""
    filename = f"{uuid.uuid4().hex[:12]}.glb"
    filepath = os.path.join(GENERATED_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(glb_bytes)
    logger.info(f"Saved GLB: {filepath} ({len(glb_bytes)} bytes)")
    return filename
