import sys
import os
import json
import networkx as nx

sys.path.insert(0, os.getcwd())

from core.schemas import BinConfig, ComponentRequest
from engine.graph_builder import build_graph
from cad_kernel.feature_executor import FeatureExecutor

print("Testing Feature Graph CAD Kernel Execution...\n")

intent = {
    "components": [
        {"id": "test_tube_16mm", "count": 4},
        {"id": "mx_switch", "count": 8},
        {"id": "raspberry_pi", "count": 1},
        {"id": "sd_card", "count": 4}
    ]
}

lib_path = os.path.join(os.path.dirname(__file__), "hardware_library", "engineering_library.json")
with open(lib_path, "r", encoding="utf-8") as f:
    component_library = json.load(f)

print(f"1. Building CAD DAG Feature Graph...")
graph = build_graph(intent, component_library, global_grid_x=3, global_grid_y=3, global_grid_z=3)

print("Execution Order:")
print(" -> " + " \n -> ".join(graph.execution_order()))

executor = FeatureExecutor()

try:
    print(f"\n2. Executing Topological Kernel Sequences...")
    result_tray = executor.execute(graph)
    
    print("\n3. Validating and Exporting Mesh...")
    from core.geometry_validator import GeometryValidator
    if not GeometryValidator.validate_manifold(result_tray):
        raise ValueError("Non-manifold mesh topology generated!")
        
    import tempfile
    import cadquery as cq
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        tmp_path = tmp.name
        
    cq.exporters.export(result_tray, tmp_path, "STL")
    size = os.path.getsize(tmp_path)
    os.remove(tmp_path)
    
    print(f"\nSUCCESS! Generated highly sophisticated multi-part STL. Size: {size} bytes.")
except Exception as e:
    import traceback
    traceback.print_exc()
