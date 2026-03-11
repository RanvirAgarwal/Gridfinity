import cadquery as cq
from features.base import build_gridfinity_base, build_walls

def create_base_tray(**kwargs):
    """
    Creates the foundational Gridfinity Tray.
    Returns exactly one Solid Workplane.
    """
    grid_x = kwargs.get("grid_x", 1)
    grid_y = kwargs.get("grid_y", 1)
    grid_z = kwargs.get("grid_z", 3)
    
    # Force single base profile block
    base_plate = build_gridfinity_base(grid_x, grid_y)
    tray = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=True, wall_thickness=2.0)
    
    return tray
