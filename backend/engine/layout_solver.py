import math
from core.constraint_solver import ConstraintSolver

def compute_layout_grid(components, component_library, max_grid_x=4):
    """
    Computes X/Y absolute coordinates for each component to avoid overlaps 
    using a 2D Row-Wrapping grid allocation strategy.
    
    Returns:
        tuple: (final_grid_x, final_grid_y, layout_placements)
    """
    component_footprints = []
    
    for comp in components:
        comp_id = comp["id"]
        count = comp["count"]
        params = component_library.get(comp_id, {})
        
        pitch = params.get("pitch", params.get("diameter", 15.0) + 4.0)
        grid_w, grid_l = ConstraintSolver.compute_grid_dimensions(count, pitch)
        
        if "arduino" in comp_id or "raspberry" in comp_id:
            grid_w, grid_l = 2, 2
            
        component_footprints.append({
            "comp": comp,
            "grid_w": grid_w,
            "grid_l": grid_l,
            "params": params
        })

    current_col = 0
    current_row = 0
    row_max_grid_y = 0
    
    layout_placements = []
    
    for fp in component_footprints:
        if current_col + fp["grid_w"] > max_grid_x and current_col > 0:
            current_row += row_max_grid_y
            current_col = 0
            row_max_grid_y = 0
            
        layout_placements.append({
            "fp": fp,
            "col": current_col,
            "row": current_row
        })
        
        current_col += fp["grid_w"]
        row_max_grid_y = max(row_max_grid_y, fp["grid_l"])

    if not layout_placements:
        return 1, 1, []

    final_grid_x = max((p["col"] + p["fp"]["grid_w"]) for p in layout_placements)
    final_grid_y = max((p["row"] + p["fp"]["grid_l"]) for p in layout_placements)
    
    # Map back to Absolute Center Coordinates
    gridfinity_unit = 42.0
    base_start_x = - (final_grid_x * gridfinity_unit) / 2.0
    base_start_y = (final_grid_y * gridfinity_unit) / 2.0
    
    placements_with_offsets = []
    for p in layout_placements:
        comp_w = p["fp"]["grid_w"]
        comp_l = p["fp"]["grid_l"]
        
        block_center_x = base_start_x + (p["col"] + comp_w / 2.0) * gridfinity_unit
        block_center_y = base_start_y - (p["row"] + comp_l / 2.0) * gridfinity_unit
        
        placements_with_offsets.append({
            "id": p["fp"]["comp"]["id"],
            "count": p["fp"]["comp"]["count"],
            "params": p["fp"]["params"],
            "comp_grid_x": comp_w,
            "comp_grid_y": comp_l,
            "offset_x": block_center_x,
            "offset_y": block_center_y
        })
        
    return final_grid_x, final_grid_y, placements_with_offsets
