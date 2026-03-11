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
    size_x = grid_x * 42.0
    size_y = grid_y * 42.0
    
    # 1 Unit height gridfinity
    tray = (
        cq.Workplane("XY")
        .rect(size_x, size_y)
        .extrude(7.0)
    )
    
    return tray
