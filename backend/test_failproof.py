import sys
import os
import json
import networkx as nx
from pathlib import Path

sys.path.insert(0, os.getcwd())

from core.schemas import BinConfig, ComponentRequest
from core.cad_engine import CadEngine
from core.graph_template_recommender import GraphTemplateRecommender

print("Testing Failproof Multi-Component CadEngine Composition...\n")

config = BinConfig(
    grid_x=3,
    grid_y=3,
    grid_z=3,
    components=[
        ComponentRequest(id="test_tube_16mm", count=4),
        ComponentRequest(id="mx_switch", count=8)
    ]
)

graph_recommender = GraphTemplateRecommender()
cadengine = CadEngine()

lib_path = os.path.join(os.path.dirname(__file__), "hardware_library", "engineering_library.json")
with open(lib_path, "r", encoding="utf-8") as f:
    component_library = json.load(f)

subgraphs = []
component_node_map = {}

for comp in config.components:
    sg = graph_recommender.suggest_template([comp.id])
    if not sg or len(sg.nodes) == 0:
        sg = graph_recommender.suggest_template(comp.id.replace("_", " ").split())
        
    if sg is not None and len(sg.nodes) > 0:
        subgraphs.append(sg)
        component_node_map[comp.id] = list(sg.nodes)

print(f"Subgraphs matched: {len(subgraphs)}")

merged_graph_dag = nx.DiGraph()
for sg in subgraphs:
    merged_graph_dag.add_nodes_from(sg.nodes)
    merged_graph_dag.add_edges_from(sg.edges)

if not nx.is_directed_acyclic_graph(merged_graph_dag):
    merged_graph_dag = nx.DiGraph(nx.topological_sort(merged_graph_dag))

print(f"Topological Execution Order: {list(nx.topological_sort(merged_graph_dag))}")

from core.constraint_solver import ConstraintSolver

total_grid_x = 0
max_grid_y = 1
component_footprints = []

for comp in config.components:
    if comp.id not in component_node_map:
        continue
    params = component_library.get(comp.id, {})
    pitch = params.get("pitch", params.get("diameter", 15.0) + 4.0)
    grid_w, grid_l = ConstraintSolver.compute_grid_dimensions(comp.count, pitch)
    
    component_footprints.append({
        "comp": comp, "grid_w": grid_w, "grid_l": grid_l, "params": params
    })
    total_grid_x += grid_w
    max_grid_y = max(max_grid_y, grid_l)

final_grid_x = max(config.grid_x, total_grid_x)
final_grid_y = max(config.grid_y, max_grid_y)

current_grid_offset = 0
gridfinity_unit = 42.0

# Inject parameters
for fp in component_footprints:
    comp = fp["comp"]
    tray_start_x = -(final_grid_x * gridfinity_unit) / 2.0
    block_center_x = tray_start_x + (current_grid_offset + fp["grid_w"] / 2.0) * gridfinity_unit
    
    for node in component_node_map[comp.id]:
        setattr(cadengine, f"{node}_params", {
            **fp["params"],
            "count": comp.count,
            "grid_x": final_grid_x,
            "grid_y": final_grid_y,
            "offset_x": block_center_x,
            "offset_y": 0.0
        })
    current_grid_offset += fp["grid_w"]

setattr(cadengine, "gridfinity_base_params", {"grid_x": final_grid_x, "grid_y": final_grid_y, "grid_z": config.grid_z})

try:
    for node in nx.topological_sort(merged_graph_dag):
        func = getattr(cadengine, node, None)
        if func is None:
            raise ValueError(f"Missing CAD kernel primitive for node: {node}")
        
        params = getattr(cadengine, f"{node}_params", {})
        print(f" -> Executing {node} with params: {params}")
        func(**params)
        
    stl = cadengine.export_stl()
    print(f"\nSUCCESS! Generated STL size: {len(stl)} bytes.")
except Exception as e:
    import traceback
    traceback.print_exc()
