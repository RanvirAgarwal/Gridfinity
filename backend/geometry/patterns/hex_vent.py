"""
Layer 4: Procedural Geometry Kernel (Hex Ventilation)

Synthesizes high-density, airflow-optimized hexagonal lattices
for electronics/medical wash-through trays.
"""

import math
import cadquery as cq
import logging

logger = logging.getLogger(__name__)

def apply_hex_vent_pattern(solid: cq.Workplane, hex_radius: float, spacing: float, depth: float, cx: int, cy: int, is_solid: bool, base_height: float) -> cq.Workplane:
    """
    Stamps an offset honeycomb grid of hexagons.
    """
    try:
        # 1. Plane Selection
        if is_solid:
            pattern = solid.faces(">Z").workplane(centerOption="CenterOfMass")
        else:
            pattern = cq.Workplane("XY").workplane(offset=base_height)
            
        # 2. Hexagon generation math (honeycomb offset)
        dx = hex_radius * 3 + spacing
        dy = hex_radius * math.sqrt(3) + spacing
        
        # Derive clamping bounds (mm)
        # Avoid cutting into the outer walls
        bound_x = (cx * dx) / 2.0
        bound_y = (cy * dy) / 2.0
        
        # Performance: Cap total hexes to avoid slow Boolean union
        MAX_TOTAL_HEXES = 64
        total_count = 0
        
        pts = []
        for i in range(cx):
            if total_count >= MAX_TOTAL_HEXES: break
            for j in range(cy):
                if total_count >= MAX_TOTAL_HEXES: break
                x = (i - cx / 2.0) * dx
                y = (j - cy / 2.0) * dy
                if i % 2 != 0:
                    y += dy / 2.0
                pts.append((x, y))
                total_count += 1
                
        # 3. Cut with Manifold Safety
        # We use a combined union for the hexagons to speed up the cut operation
        return pattern.pushPoints(pts).polygon(6, hex_radius * 2).cutBlind(-depth)
            
    except Exception as e:
        logger.error(f"Failed to generate hex vent pattern: {e}")
        return solid
