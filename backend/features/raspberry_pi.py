import cadquery as cq

def add_raspberry_pi_mount(tray: cq.Workplane, **kwargs) -> cq.Workplane:
    """
    Modifies the single tray solid by adding standoffs for Raspberry Pi.
    """
    offset_x = kwargs.get("offset_x", 0.0)
    offset_y = kwargs.get("offset_y", 0.0)
    
    # Standard Pi mounting holes relative to its origin
    holes = [
        (3.5, 3.5),
        (61.5, 3.5),
        (3.5, 52.5),
        (61.5, 52.5)
    ]
    
    # Center the footprint at offset_x, offset_y
    # Pi total dim: 85x56
    aligned_holes = [(x - 42.5 + offset_x, y - 28.0 + offset_y) for x, y in holes]
    print(f"Executing Raspberry Pi Mount at points: {aligned_holes}")
    
    standoffs = (
        cq.Workplane("XY")
        .workplane(offset=7.0)  # Absolute offset matches 7.0 minimal box base height exactly
        .pushPoints(aligned_holes)
        .circle(3.0)
        .extrude(5.0)
        .faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .circle(1.5)
        .cutBlind(-5.0)
    )
    
    return tray.union(standoffs)
