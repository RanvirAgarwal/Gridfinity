import logging
import cadquery as cq

logger = logging.getLogger(__name__)

class GeometryValidator:
    """
    Validates CAD features before final generation/export.
    Prevents OpenCASCADE from crashing on disallowed planar slices
    or boundary violations.
    """
    
    @staticmethod
    def validate_points_in_bounds(pts: list[tuple[float, float]], feature_radius: float, grid_x: int, grid_y: int, min_wall: float = 2.0) -> bool:
        """
        Checks if an array of cuts will violate the outer walls of the bin.
        Returns False if any point + its radius breaches the boundary.
        """
        # Gridfinity blocks are centered at (0,0) in our engine
        # Outer boundary is (grid_x * 42) x (grid_y * 42)
        max_x = (grid_x * 42.0) / 2.0 - min_wall
        max_y = (grid_y * 42.0) / 2.0 - min_wall
        
        for px, py in pts:
            if abs(px) + feature_radius > max_x:
                logger.error(f"Geometry Validation Failed: Point ({px}, {py}) with radius {feature_radius} violates X boundary {max_x}.")
                return False
            if abs(py) + feature_radius > max_y:
                logger.error(f"Geometry Validation Failed: Point ({px}, {py}) with radius {feature_radius} violates Y boundary {max_y}.")
                return False
                
        return True

    @staticmethod
    def validate_manifold(solid: cq.Workplane) -> bool:
        """
        Ensures the final B-Rep solid is mathematically valid and manifold
        before passing it to the STL exporter.
        """
        try:
            # cadquery val().isValid() checks underlying OpenCASCADE shape integrity
            if not solid.val().isValid():
                logger.error("Geometry Validation Failed: Generated shape is not valid (non-manifold or disjoint geometry).")
                return False
            return True
        except Exception as e:
            logger.error(f"Geometry Validation Exception during manifold check: {e}")
            return False
