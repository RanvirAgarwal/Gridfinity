"""
Layer 2: Parametric Constraint Engine
Validates user payloads to prevent the model from creating structurally unsound,
impossible to print, or non-manifold topology.
"""

import logging
from core.schemas import BinConfig

logger = logging.getLogger(__name__)

class ConstraintEngine:
    MIN_WALL_THICKNESS = 1.2
    MIN_FLOOR_THICKNESS = 2.0
    GRID_UNIT = 42.0
    HEIGHT_STEP = 7.0
    MAX_GRID_X = 6
    MAX_GRID_Y = 6
    MAX_REPEAT_CAP = 16

    # Mechanical Tolerance Library (mm)
    TOLERANCE_PRESS_FIT = 0.05
    TOLERANCE_TIGHT_FIT = 0.1
    TOLERANCE_SLIP_FIT = 0.2
    TOLERANCE_LOOSE_FIT = 0.5

    @classmethod
    def apply_scale(cls, value: float, max_bound: float) -> float:
        """
        Ensures a value is strictly within mm scale and respects the physical 
        bounds of the parent grid. Blocks 'unit explosion'.
        """
        if value > max_bound:
            return max_bound
        return max(0.1, value)

    @classmethod
    def validate_and_clamp(cls, config: BinConfig) -> BinConfig:
        """
        Actively modifies the generated LLM values in-memory to forcibly
        guarantee mechanical manufacturability.
        """
        # 1. Clamp macroscopic grid dimensions to prevent massive bed overhangs
        if config.grid_x < 1:
            logger.warning("Clamping grid_x from < 1 to 1")
            config.grid_x = 1
        elif config.grid_x > cls.MAX_GRID_X:
            logger.warning(f"Clamping grid_x from {config.grid_x} to {cls.MAX_GRID_X}")
            config.grid_x = cls.MAX_GRID_X

        if config.grid_y < 1:
            logger.warning("Clamping grid_y from < 1 to 1")
            config.grid_y = 1
        elif config.grid_y > cls.MAX_GRID_Y:
            logger.warning(f"Clamping grid_y from {config.grid_y} to {cls.MAX_GRID_Y}")
            config.grid_y = cls.MAX_GRID_Y

        # 2. Derive physical bounds for relative clamping
        max_w = config.grid_x * cls.GRID_UNIT - 4.0 
        max_l = config.grid_y * cls.GRID_UNIT - 4.0
        max_h = (config.grid_z * cls.HEIGHT_STEP) + 10.0

        # 3. Iterate through operations array and sanitize depths / widths / counts
        for op in config.operations:
            op_type = op.get("type", "")
            
            # Performance: Cap total boolean repetitions
            if "count" in op: op["count"] = min(op["count"], cls.MAX_REPEAT_CAP)
            if "count_x" in op: op["count_x"] = min(op["count_x"], 4)
            if "count_y" in op: op["count_y"] = min(op["count_y"], 4)

            if op_type == "drill_wall":
                op["diameter"] = cls.apply_scale(op.get("diameter", 5.0), max_h / 2.0)
            
            elif op_type == "cut_array":
                op["depth"] = cls.apply_scale(op.get("depth", 2.0), max_h - cls.MIN_FLOOR_THICKNESS)
                if op.get("shape") == "cylinder":
                    op["size_x"] = cls.apply_scale(op.get("size_x", 5.0), max_w / 4.0)
                else:
                    op["size_x"] = cls.apply_scale(op.get("size_x", 10.0), max_w / 2.0)
                    op["size_y"] = cls.apply_scale(op.get("size_y", 10.0), max_l / 2.0)

            elif op_type == "hex_vent":
                op["radius"] = cls.apply_scale(op.get("radius", 2.0), 5.0) 
                if op.get("spacing", 0) < 0.8: op["spacing"] = 1.0 
                op["depth"] = cls.apply_scale(op.get("depth", 2.0), max_h - cls.MIN_FLOOR_THICKNESS)

            elif op_type == "slot_array":
                op["comp_width"] = cls.apply_scale(op.get("comp_width", 30.0), max_w - 2.0)
                op["comp_thickness"] = cls.apply_scale(op.get("comp_thickness", 2.0), 20.0)
                op["comp_height"] = cls.apply_scale(op.get("comp_height", 20.0), 100.0)
                # Enforce minimum 0.5mm clearance for real-world fitment
                op["clearance"] = max(op.get("clearance", 0.5), 0.5)

            elif op_type == "cable_channel":
                op["width"] = cls.apply_scale(op.get("width", 8.0), 20.0)
                op["depth"] = cls.apply_scale(op.get("depth", 5.0), max_h - 2.0)

            elif op_type == "standoffs":
                op["diameter"] = cls.apply_scale(op.get("diameter", 5.0), 10.0)
                op["height"] = cls.apply_scale(op.get("height", 5.0), max_h / 2.0)

        return config

    @classmethod
    def get_tolerance(cls, fit_type: str) -> float:
        """Helper router to fetch the exact clearance (in mm) from the dictionary."""
        mapping = {
            "press_fit": cls.TOLERANCE_PRESS_FIT,
            "tight_fit": cls.TOLERANCE_TIGHT_FIT,
            "slip_fit": cls.TOLERANCE_SLIP_FIT,
            "loose_fit": cls.TOLERANCE_LOOSE_FIT
        }
        return mapping.get(fit_type, cls.TOLERANCE_SLIP_FIT)
