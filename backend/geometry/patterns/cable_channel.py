"""
Layer 4: Procedural Geometry Kernel (Cable Channels)

Creates routing trenches for electronics grids.
"""

import cadquery as cq
import logging

logger = logging.getLogger(__name__)

def apply_cable_channel(solid: cq.Workplane, width: float, depth: float, axis: str, is_solid: bool, base_height: float) -> cq.Workplane:
    """
    Cuts a trough across the specified axis.
    """
    try:
        if is_solid:
            pattern = solid.faces(">Z").workplane(centerOption="CenterOfMass")
        else:
            pattern = cq.Workplane("XY").workplane(offset=base_height)
            
        cutter = pattern.rect(200, width) if axis == 'X' else pattern.rect(width, 200)
        return cutter.cutBlind(-depth)
        
    except Exception as e:
        logger.error(f"Failed to generate cable channel: {e}")
        return solid
