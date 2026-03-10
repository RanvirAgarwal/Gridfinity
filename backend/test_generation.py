import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, os.getcwd())

from core.schemas import BinConfig, ComponentRequest
from core.cadquery_engine import _cq_build_bin, generate_stl
from core.learning_engine import LearningEngine

# Simulate the configuration for a test tube rack and an MX switch
config = BinConfig(
    grid_x=2,
    grid_y=3,
    grid_z=4,
    template_name="test_tube_rack_16mm",
    components=[
        ComponentRequest(id="test_tube_16mm", count=16)
    ]
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
    
    # Simulate Learning Engine recipe tracking
    recipe = {
        "prompt": "simulated test run",
        "component": config.component_id,
        "count": config.item_count,
        "template": config.template_name,
        "feature_graph": [
            {"feature": "gridfinity_base", "params": {"grid_x": config.grid_x, "grid_y": config.grid_y}},
            {"feature": config.template_name, "params": {}}
        ],
        "status": "valid"
    }
    le = LearningEngine()
    le.record_generation(recipe)
    print("SUCCESS: Feature graph serialized to learning_recipes/")
    
    
except Exception as e:
    print(f"\nGENERATION ERROR: {e}")
    import traceback
    traceback.print_exc()
