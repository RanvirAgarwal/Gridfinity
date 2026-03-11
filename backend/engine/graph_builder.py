from cad_kernel.feature_graph import FeatureGraph
from engine.layout_solver import compute_layout_grid
from core.graph_template_recommender import GraphTemplateRecommender
import networkx as nx

def build_graph(intent_dict, component_library, global_grid_x=1, global_grid_y=1, global_grid_z=3):
    """
    Constructs the directed acyclic graph (DAG) of pure geometric features.
    Enforces the single root base tray constraint.
    """
    g = FeatureGraph()
    recommender = GraphTemplateRecommender()
    
    components = intent_dict.get("components", [])
    print(f"Graph Builder - Components detected: {components}")
    
    # Calculate geometric absolute bounding positions securely via 2D algorithm
    max_grid_x_per_row = max(global_grid_x, 4)
    final_grid_x, final_grid_y, placements = compute_layout_grid(components, component_library, max_grid_x_per_row)
    
    # 1. Base Node
    g.add_feature("base_tray", params={
        "grid_x": max(final_grid_x, global_grid_x), 
        "grid_y": max(final_grid_y, global_grid_y), 
        "grid_z": global_grid_z
    })
    
    # 2. Extract mappings for each placement
    for p in placements:
        comp_id = p["id"]
        
        # Get matching subgraph nodes for this component ID from Recommender Engine
        sg = recommender.suggest_template([comp_id])
        if not sg or len(sg.nodes) == 0:
            sg = recommender.suggest_template(comp_id.replace("_", " ").split())
            
        nodes_to_execute = list(sg.nodes) if sg and len(sg.nodes) > 0 else [comp_id]
        
        # Sequentially attach each required primitive node as dependent on the base_tray
        for node in nodes_to_execute:
            # Skip redundant foundational macros since the root DAG node already allocated `base_tray`
            if node in ["gridfinity_base", "basic_storage_bin", "base_tray"]:
                continue
                
            node_id = f"{node}_{p['offset_x']}_{p['offset_y']}" # guarantee uniqueness per position
            g.add_feature(
                node_id, 
                feature_name=node, 
                params={
                    **p["params"],
                    "count": p["count"],
                    "comp_grid_x": p["comp_grid_x"],
                    "comp_grid_y": p["comp_grid_y"],
                    "offset_x": p["offset_x"],
                    "offset_y": p["offset_y"],
                    "grid_x": final_grid_x,
                    "grid_y": final_grid_y,
                    "grid_z": global_grid_z
                }
            )
            g.add_dependency("base_tray", node_id)

    return g
