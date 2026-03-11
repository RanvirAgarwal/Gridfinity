import cadquery as cq
from core.constraint_solver import ConstraintSolver
from core.geometry_validator import GeometryValidator

HEIGHT_UNIT = 7.0
BASE_HEIGHT = 4.75 

def add_test_tube_rack(tray: cq.Workplane, **kwargs) -> cq.Workplane:
    """
    Modifies the existing tray Solid by cutting cylindrical holes for test tubes.
    """
    grid_x = kwargs.get("grid_x", 1)
    grid_y = kwargs.get("grid_y", 1)
    grid_z = kwargs.get("grid_z", 3)
    
    count = kwargs.get("count", 10)
    diameter = kwargs.get("diameter", 16.0)
    pitch = ConstraintSolver.calculate_pitch(diameter, 4.0)
    
    rows, cols, start_x, start_y = ConstraintSolver.calculate_array_bounds(count, pitch)
    
    offset_x = kwargs.get("offset_x", 0.0)
    offset_y = kwargs.get("offset_y", 0.0)
    
    pts = []
    placed = 0
    for r in range(rows):
        for c in range(cols):
            if placed >= count: break
            pts.append((start_x + c * pitch + offset_x, start_y - r * pitch + offset_y))
            placed += 1
            
    hole_diam = ConstraintSolver.calculate_hole_diameter(diameter, is_press_fit=False)
    GeometryValidator.validate_points_in_bounds(pts, hole_diam / 2.0, grid_x, grid_y)
    
    radius = hole_diam / 2.0
    print(f"Executing Test Tube Holes at points: {pts}") # Debug explicit verification
    
    # Failproof CUT logic natively evaluated along the CenterOfMass of the flat top face
    wp = tray.faces(">Z").workplane(centerOption="CenterOfMass")
    tray = (
        wp.pushPoints(pts)
        .circle(radius)
        .cutThruAll()
    )
    
    return tray
