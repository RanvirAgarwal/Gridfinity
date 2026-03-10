import math
import logging

logger = logging.getLogger(__name__)

class ConstraintSolver:
    """
    Centralized solver for engineering constraints and geometric tolerances.
    Replaces hardcoded math throughout templates.
    """
    GRIDFINITY_UNIT_XY = 42.0
    GRIDFINITY_UNIT_Z = 7.0
    MIN_WALL_THICKNESS = 2.0
    CLEARANCE_SLIP = 0.4
    CLEARANCE_PRESS = 0.2
    BASE_HEIGHT = 4.75
    
    @classmethod
    def calculate_hole_diameter(cls, component_diameter: float, is_press_fit: bool = False) -> float:
        """Returns the manufacturable diameter for a circular cut."""
        clearance = cls.CLEARANCE_PRESS if is_press_fit else cls.CLEARANCE_SLIP
        # Add diametral clearance
        return component_diameter + (clearance * 2.0)
        
    @classmethod
    def calculate_pitch(cls, component_width: float, min_wall: float = None) -> float:
        """Calculates the safe minimum pitch space between two repeated elements."""
        wall = min_wall if min_wall is not None else cls.MIN_WALL_THICKNESS
        return component_width + wall
        
    @classmethod
    def compute_grid_dimensions(cls, item_count: int, pitch_x: float, pitch_y: float = None) -> tuple[int, int]:
        """
        Determines the minimum Gridfinity X,Y units required to contain
        a specific number of items spaced by a given pitch.
        """
        if pitch_y is None:
            pitch_y = pitch_x
            
        slots = item_count if item_count and item_count > 0 else 1
        cols = math.ceil(math.sqrt(slots))
        rows = math.ceil(slots / cols)
        
        # Add 10mm padding for exterior walls and tolerances
        min_grid_x = math.ceil((cols * pitch_x + 10.0) / cls.GRIDFINITY_UNIT_XY)
        min_grid_y = math.ceil((rows * pitch_y + 10.0) / cls.GRIDFINITY_UNIT_XY)
        
        return (int(min_grid_x), int(min_grid_y))

    @classmethod
    def calculate_array_bounds(cls, item_count: int, pitch_x: float, pitch_y: float = None) -> tuple[int, int, float, float]:
        """Returns (rows, cols, start_x, start_y) for centering an array in a grid."""
        if pitch_y is None:
            pitch_y = pitch_x
            
        slots = item_count if item_count and item_count > 0 else 1
        cols = math.ceil(math.sqrt(slots))
        rows = math.ceil(slots / cols)
        
        start_x = -((cols - 1) * pitch_x) / 2.0
        start_y = ((rows - 1) * pitch_y) / 2.0
        
        return rows, cols, start_x, start_y
