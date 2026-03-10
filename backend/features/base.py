"""
Layer 3: Trusted Template Library (Gridfinity Base)
Produces a standard, deterministic 42mm Gridfinity manifold base.
"""

import cadquery as cq
from core.constraint_engine import ConstraintEngine

# Replicate the core Gridfinity constants
GRID_UNIT = ConstraintEngine.GRID_UNIT
HEIGHT_UNIT = ConstraintEngine.HEIGHT_STEP
BASE_HEIGHT = 4.75 
LIP_HEIGHT = 4.0
CORNER_RADIUS = 3.8
BASE_CLEARANCE = ConstraintEngine.get_tolerance("slip_fit")

def build_gridfinity_base(grid_x: int, grid_y: int) -> cq.Workplane:
    """
    Constructs the foundational 42x42mm interlocking Gridfinity base.
    Uses safe, clamped dimensions from the constraint engine.
    """
    total_w = grid_x * GRID_UNIT - BASE_CLEARANCE * 2
    total_l = grid_y * GRID_UNIT - BASE_CLEARANCE * 2

    # 1. Main Base Square
    base = (
        cq.Workplane("XY")
        .box(total_w, total_l, 0.8, centered=(True, True, False))
        .edges("|Z")
        .fillet(CORNER_RADIUS)
    )

    # 2. Add the 42mm Grid Profile array
    profile = (
        cq.Workplane("XY")
        .workplane(offset=0.8)
        .rarray(GRID_UNIT, GRID_UNIT, grid_x, grid_y)
        .rect(GRID_UNIT - 0.5, GRID_UNIT - 0.5)
        .extrude(3.95)
    )
    
    try:
        profile = profile.edges("|Z").fillet(2.5)
        profile = profile.faces(">Z").chamfer(0.8)
    except Exception:
        pass  # Failsafe for complex topology overlap

    return base.union(profile)

def build_walls(base_plate: cq.Workplane, grid_x: int, grid_y: int, height_units: int, is_solid: bool, wall_thickness: float = 2.0) -> cq.Workplane:
    """
    Builds either a massive solid block or a hollow bin cavity on top of the base plate.
    """
    outer_w = grid_x * GRID_UNIT - BASE_CLEARANCE * 2
    outer_l = grid_y * GRID_UNIT - BASE_CLEARANCE * 2
    wall_height = height_units * HEIGHT_UNIT

    walls = (
        cq.Workplane("XY")
        .workplane(offset=BASE_HEIGHT)
        .box(outer_w, outer_l, wall_height + LIP_HEIGHT, centered=(True, True, False))
        .edges("|Z")
        .fillet(CORNER_RADIUS)
    )

    if is_solid:
        return base_plate.union(walls)

    # Hollow out the interior
    interior_w = outer_w - wall_thickness * 2
    interior_l = outer_l - wall_thickness * 2
    interior = (
        cq.Workplane("XY")
        .workplane(offset=BASE_HEIGHT)
        .box(interior_w, interior_l, wall_height + LIP_HEIGHT + 1, centered=(True, True, False))
        .edges("|Z")
        .fillet(max(0.1, CORNER_RADIUS - wall_thickness))
    )

    return base_plate.union(walls).cut(interior)
