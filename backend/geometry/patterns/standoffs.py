"""
Layer 4: Procedural Geometry Kernel (Standoff Mounts)

Builds rigid press-fit pegs dynamically sized to PCB mounting holes.
"""

import cadquery as cq
import logging

logger = logging.getLogger(__name__)

def apply_standoffs(solid: cq.Workplane, holes: list, diameter: float, height: float, is_solid: bool, base_height: float) -> cq.Workplane:
    """
    Creates multiple cylindrical standoffs for mounting boards.
    """
    try:
        if is_solid:
            pattern = solid.faces(">Z").workplane(centerOption="CenterOfMass")
        else:
            pattern = cq.Workplane("XY").workplane(offset=base_height)
            
        pts = [(h['x'], h['y']) for h in holes]
        return pattern.pushPoints(pts).circle(diameter/2.0).extrude(height)
        
    except Exception as e:
        logger.error(f"Failed to generate standoffs: {e}")
        return solid
