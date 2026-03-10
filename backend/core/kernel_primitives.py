import cadquery as cq
import logging
import math

logger = logging.getLogger(__name__)

class KernelPrimitives:
    """
    Procedural Geometry Kernel.
    Wraps raw CadQuery operations into reusable, reliable CAD macros.
    """
    BASE_HEIGHT = 4.75
    HEIGHT_UNIT = 7.0
    
    @staticmethod
    def create_solid_block(base_plate: cq.Workplane, grid_x: int, grid_y: int, grid_z: int) -> cq.Workplane:
        """Creates a completely solid Gridfinity block spanning the requested grid layout."""
        outer_w = grid_x * 42.0 - 0.5
        outer_l = grid_y * 42.0 - 0.5
        total_height = grid_z * KernelPrimitives.HEIGHT_UNIT
        
        block = (
            cq.Workplane("XY")
            .workplane(offset=KernelPrimitives.BASE_HEIGHT)
            .rect(outer_w, outer_l)
            .extrude(total_height)
        )
        return base_plate.union(block)
        
    @staticmethod
    def apply_angled_cut(solid: cq.Workplane, grid_x: int, grid_y: int, grid_z: int, angle: float) -> cq.Workplane:
        """Applies an explicit boolean wedge cut to slope the top face of a solid block."""
        outer_w = grid_x * 42.0 - 0.5
        outer_l = grid_y * 42.0 - 0.5
        total_height = grid_z * KernelPrimitives.HEIGHT_UNIT
        
        cutter = (
            cq.Workplane("XY")
            .workplane(offset=KernelPrimitives.BASE_HEIGHT + total_height) 
            .transformed(rotate=(-angle, 0, 0))
            .rect(outer_w * 3, outer_l * 3)
            .extrude(total_height + 20)
        )
        return solid.cut(cutter)
        
    @staticmethod
    def circular_array_cut(solid: cq.Workplane, pts: list[tuple[float, float]], diameter: float, depth: float) -> cq.Workplane:
        """Pushes an exact array of circular blind cuts."""
        if not pts:
            return solid
        radius = diameter / 2.0
        return solid.faces(">Z").workplane(centerOption="CenterOfMass").pushPoints(pts).circle(radius).cutBlind(-abs(depth))

    @staticmethod
    def rectangular_array_cut(solid: cq.Workplane, pts: list[tuple[float, float]], width: float, length: float, depth: float) -> cq.Workplane:
        """Pushes an exact array of rectangular blind cuts."""
        if not pts:
            return solid
        return solid.faces(">Z").workplane(centerOption="CenterOfMass").pushPoints(pts).rect(width, length).cutBlind(-abs(depth))
        
    @staticmethod
    def add_divider_wall(solid: cq.Workplane, grid_y: int, grid_z: int, wall_thickness: float = 2.0) -> cq.Workplane:
        """Generates a divider wall down the Y centerline of a hollow bin."""
        length = grid_y * 42.0 - 4.0
        total_height = grid_z * KernelPrimitives.HEIGHT_UNIT
        divider = (
            cq.Workplane("XY")
            .workplane(offset=KernelPrimitives.BASE_HEIGHT)
            .rect(wall_thickness, length)
            .extrude(total_height - KernelPrimitives.BASE_HEIGHT)
        )
        return solid.union(divider)
