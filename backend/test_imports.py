import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, os.getcwd())

try:
    from core.schemas import BinConfig
    print("SUCCESS: core.schemas imported")
    from ai.openrouter_engine import AdvancedGenerateRequest
    print("SUCCESS: ai.openrouter_engine imported")
    from core.cadquery_engine import generate_stl
    print("SUCCESS: core.cadquery_engine imported")
    from features.base import build_gridfinity_base
    print("SUCCESS: features.base imported")
    from geometry.patterns.hex_vent import apply_hex_vent_pattern
    print("SUCCESS: geometry.patterns.hex_vent imported")
    print("\nALL SYSTEM IMPORTS VERIFIED")
except Exception as e:
    print(f"\nIMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
