import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, os.getcwd())

from core.schemas import BinConfig
from core.cadquery_engine import _cq_build_bin, generate_stl

# Simulate the configuration for a test tube rack
config = BinConfig(
    grid_x=1,
    grid_y=1,
    grid_z=3,
    template_name="mx_switch_tester"
)

try:
    print("Starting stand-alone generation test...")
    model = _cq_build_bin(config)
    print("SUCCESS: _cq_build_bin completed")
    
    # Try the export to find where it's failing
    import tempfile
    import cadquery as cq
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        tmp_path = tmp.name
    
    cq.exporters.export(model, tmp_path, "STL")
    print(f"SUCCESS: STL exported to {tmp_path}")
    os.remove(tmp_path)
    
except Exception as e:
    print(f"\nGENERATION ERROR: {e}")
    import traceback
    traceback.print_exc()
