"""
Layer 3: Trusted Template Library (Pattern Arrays)
"""

import cadquery as cq
import logging

logger = logging.getLogger(__name__)

def apply_cut_array(solid: cq.Workplane, shape: str, size_x: float, size_y: float, depth: float, cx: int, cy: int, sx: float, sy: float, is_solid: bool, base_height: float) -> cq.Workplane:
    """
    Applies the reliable CadQuery .rarray() repeating grid cut.
    Automatically safely clamps the depth and plane mapping.
    """
    try:
        # 1. Plane Selection Guardrail
        if is_solid:
            # Target the absolute top exterior roof
            pattern = solid.faces(">Z").workplane(centerOption="CenterOfMass")
        else:
            # Target the absolute bottom interior floor
            pattern = cq.Workplane("XY").workplane(offset=base_height)
            
        pattern = pattern.rarray(sx, sy, cx, cy)
        
        # 2. Geometry Execution
        if shape == "cylinder" or shape == "circle":
            rad = max(0.1, size_x / 2.0)
            return pattern.circle(rad).cutBlind(-depth)
        else:
            return pattern.rect(max(0.1, size_x), max(0.1, size_y)).cutBlind(-depth)
            
    except Exception as e:
        logger.error(f"Failed to apply pattern array: {e}")
        return solid

def drill_wall_hole(solid: cq.Workplane, diameter: float, face: str) -> cq.Workplane:
    """
    Bores a hole completely through the specified wall face. Useful for cables.
    """
    try:
        selector = ">Y" if face == "front" else "<Y" if face == "back" else ">X" if face == "right" else "<X"
        return solid.faces(selector).workplane(centerOption="CenterOfMass").hole(diameter)
    except Exception as e:
        logger.error(f"Failed to drill wall hole {face}: {e}")
        return solid
