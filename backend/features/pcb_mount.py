"""
Layer 3: Trusted Template Library (PCB Mount)
Generates physical parametric standoffs and mounting holes for components like an Arduino Uno.
"""

import cadquery as cq
import logging

logger = logging.getLogger(__name__)

def build_pcb_mount(component_db_spec: dict, base_z_offset: float) -> cq.Workplane:
    """
    Generates elevated standoffs with screw holes dynamically based on the 
    Layer 1 component DB JSON payload array.
    """
    holes = component_db_spec.get("mount_holes", [])
    if not holes:
        logger.warning(f"No mount_holes found in component DB spec for PCB mount.")
        return cq.Workplane("XY")

    # The geometric center of the board needs to be calculated to align it with the bin
    # We assume the mount holes in JSON are from the board's bottom-left (0,0)
    # To center the board at world (0,0), we subtract length/2 and width/2
    length = component_db_spec.get("length", 68.6)
    width = component_db_spec.get("width", 53.4)
    offset_x = -length / 2.0
    offset_y = -width / 2.0

    # Standoff dimensions
    standoff_radius = 2.5
    standoff_height = 5.0
    screw_hole_radius = 1.45 # M3 tap hole is ~2.9mm
    
    # Generate the physical assembly
    # We add a 0.1mm sink into the base_z to ensure a clean manifold union
    standoffs = (
        cq.Workplane("XY")
        .workplane(offset=base_z_offset - 0.1)
        .pushPoints([(h["x"] + offset_x, h["y"] + offset_y) for h in holes])
        .circle(standoff_radius)
        .extrude(standoff_height + 0.1)
        .faces(">Z")
        .workplane()
        .circle(screw_hole_radius)
        .cutBlind(-standoff_height)
    )

    return standoffs
