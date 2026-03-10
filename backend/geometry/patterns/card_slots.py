"""
Layer 4: Procedural Geometry Kernel (Slot Arrays)

Auto-generates precision parametric arrays for organizing objects
like SD cards, game cartridges, rings, or PCBs based on their Component DB dimensions.
"""

import cadquery as cq
import logging

logger = logging.getLogger(__name__)

def apply_slotted_array(solid: cq.Workplane, comp_width: float, comp_height: float, comp_thickness: float, clearance: float, count: int, is_solid: bool, base_height: float) -> cq.Workplane:
    """
    Dynamically sizes slot bounds based on target component.
    """
    try:
        # Mandatory minimum clearance for real-world fitment (Slip Fit)
        effective_clearance = max(clearance, 0.5)
        
        slot_w = comp_width + (effective_clearance * 2)
        slot_l = comp_thickness + (effective_clearance * 2)
        slot_depth = comp_height * 0.4 # Typical grab ratio
        
        # Performance: Cap total slots to 16
        safe_count = min(count, 16)
        
        spacing_y = slot_l + 3.0 # Min wall thickness between slots
        
        return pattern.rarray(slot_w + 3.0, spacing_y, 1, safe_count).rect(slot_w, slot_l).cutBlind(-slot_depth)
        
    except Exception as e:
        logger.error(f"Failed to generate slot array: {e}")
        return solid
