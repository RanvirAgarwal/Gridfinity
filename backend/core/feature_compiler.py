"""
Layer 4: Feature Compiler
The "Translator" that maps abstract LLM operations into concrete 
Geometry Kernel function calls.
"""

import logging
import cadquery as cq
from components import database
from features.pcb_mount import build_pcb_mount
from geometry.patterns.tilt import apply_tilted_slice
from geometry.patterns.array import apply_cut_array, drill_wall_hole
from geometry.patterns.hex_vent import apply_hex_vent_pattern
from geometry.patterns.card_slots import apply_slotted_array
from geometry.patterns.cable_channel import apply_cable_channel
from geometry.patterns.standoffs import apply_standoffs

logger = logging.getLogger(__name__)

class FeatureCompiler:
    @staticmethod
    def apply_operations(model: cq.Workplane, operations: list, is_solid: bool, base_height: float) -> cq.Workplane:
        """
        Iteratively applies the feature grammar to the manifold B-Rep solid.
        """
        for op in operations:
            op_type = op.get("type")
            logger.info(f"Compiling feature: {op_type}")
            
            try:
                if op_type == "template":
                    comp_key = op.get("name", "")
                    if comp_key:
                        try:
                            db_spec = database.lookup(comp_key)
                            cat = db_spec.get("category", "")
                            if cat in ["microcontroller", "electronics"]:
                                standoffs = build_pcb_mount(db_spec, base_height)
                                model = model.union(standoffs)
                        except Exception as e:
                            logger.warning(f"Template compilation failed: {e}")

                elif op_type == "angle_slice":
                    model = apply_tilted_slice(model, op.get("angle", 0))
                
                elif op_type == "cut_array":
                    model = apply_cut_array(
                        model, 
                        op.get("size_x", 5), 
                        op.get("size_y", 5), 
                        op.get("depth", 2), 
                        op.get("count_x", 1), 
                        op.get("count_y", 1), 
                        op.get("spacing_x", 10), 
                        op.get("spacing_y", 10), 
                        op.get("shape", "square"),
                        is_solid,
                        base_height
                    )
                
                elif op_type == "drill_wall":
                    model = drill_wall_hole(
                        model, 
                        op.get("diameter", 5), 
                        op.get("face", "front")
                    )

                elif op_type == "hex_vent":
                    model = apply_hex_vent_pattern(
                        model,
                        op.get("radius", 2.0),
                        op.get("spacing", 1.0),
                        op.get("depth", 2.0),
                        op.get("cx", 5),
                        op.get("cy", 5),
                        is_solid,
                        base_height
                    )

                elif op_type == "slot_array":
                    model = apply_slotted_array(
                        model,
                        op.get("comp_width", 30.0),
                        op.get("comp_height", 20.0),
                        op.get("comp_thickness", 2.0),
                        op.get("clearance", 0.2),
                        op.get("count", 3),
                        is_solid,
                        base_height
                    )

                elif op_type == "cable_channel":
                    model = apply_cable_channel(
                        model,
                        op.get("width", 8.0),
                        op.get("depth", 5.0),
                        op.get("axis", "X"),
                        is_solid,
                        base_height
                    )

                elif op_type == "standoffs":
                    model = apply_standoffs(
                        model,
                        op.get("holes", []),
                        op.get("diameter", 5.0),
                        op.get("height", 5.0),
                        is_solid,
                        base_height
                    )

            except Exception as e:
                logger.error(f"Feature compilation failed for {op_type}: {e}")
                
        return model
