"""
Layer 3: Trusted Template Library (Angled Retail Displays)
"""

import math
import cadquery as cq

def compute_tilt_height(depth_mm: float, angle_degrees: float) -> float:
    """
    y = x * tan(theta)
    Trigonometric calculation for retail angled displays.
    """
    angle_rad = math.radians(angle_degrees)
    vertical_rise = depth_mm * math.tan(angle_rad)
    return vertical_rise

def apply_tilted_slice(solid: cq.Workplane, angle_degrees: float) -> cq.Workplane:
    """
    Takes a solid block and forcefully trims it at the specified angle.
    """
    if angle_degrees <= 0 or angle_degrees >= 90:
        return solid

    try:
        sliced_solid = (
            solid.faces(">Z").workplane(centerOption="CenterOfMass")
            .transformed(rotate=(angle_degrees, 0, 0))
            .split(keepTop=False, keepBottom=True)
        )
        return sliced_solid
    except Exception:
        return solid
