import cadquery as cq
from core.constraint_solver import ConstraintSolver
from core.geometry_validator import GeometryValidator

HEIGHT_UNIT = 7.0
BASE_HEIGHT = 4.75 

def add_mx_switch_tester(tray: cq.Workplane, **kwargs) -> cq.Workplane:
    """
    Modifies the single tray solid by carving a sloped surface and grid cuts for MX switches.
    """
    grid_x = kwargs.get("grid_x", 1)
    grid_y = kwargs.get("grid_y", 1)
    grid_z = kwargs.get("grid_z", 3)
    
    comp_grid_x = kwargs.get("comp_grid_x", grid_x)
    comp_grid_y = kwargs.get("comp_grid_y", grid_y)
    offset_x = kwargs.get("offset_x", 0.0)
    offset_y = kwargs.get("offset_y", 0.0)
    
    angle = kwargs.get("tilt", 15.0)
    outer_w = comp_grid_x * 42.0
    outer_l = comp_grid_y * 42.0
    tot_h = grid_z * HEIGHT_UNIT
    
    cutter = (
        cq.Workplane("XY")
        .workplane(offset=BASE_HEIGHT + tot_h) 
        .center(offset_x, offset_y)
        .transformed(rotate=(-angle, 0, 0))
        .rect(outer_w + 1.0, outer_l + 1.0)
        .extrude(tot_h + 20)
    )
    # Cut sloped face only in bounded cell allocation
    tray = tray.cut(cutter)
    
    count = kwargs.get("count", 16)
    pitch = kwargs.get("pitch", 19.05)
    body_size = kwargs.get("body", 14.0)
    
    rows, cols, start_x, start_y = ConstraintSolver.calculate_array_bounds(count, pitch)
    
    pts = []
    placed = 0
    for r in range(rows):
        for c in range(cols):
            if placed >= count: break
            pts.append((start_x + c * pitch + offset_x, start_y - r * pitch + offset_y))
            placed += 1
            
    GeometryValidator.validate_points_in_bounds(pts, body_size / 2.0, grid_x, grid_y)
    tray = tray.faces(">Z").workplane(centerOption="CenterOfMass").pushPoints(pts).rect(body_size, body_size).cutBlind(-6.0)
    return tray
