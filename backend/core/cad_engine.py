import os
import tempfile
import logging
import cadquery as cq

from core.constraint_solver import ConstraintSolver
from core.geometry_validator import GeometryValidator
from features.base import build_gridfinity_base, build_walls

logger = logging.getLogger(__name__)

class CadEngine:
    """
    Stateful CAD kernel that maintains the boolean B-Rep operations
    across topological feature graph executions.
    """
    BASE_HEIGHT = 4.75
    HEIGHT_UNIT = 7.0

    def __init__(self):
        self.solid = None
        self.base_plate = None
        self.grid_x = 1
        self.grid_y = 1
        self.grid_z = 3
        
    def gridfinity_base(self, grid_x: int=1, grid_y: int=1, grid_z: int=3, **kwargs):
        logger.info(f"CadEngine executing: gridfinity_base {grid_x}x{grid_y}x{grid_z}")
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.grid_z = grid_z
        self.base_plate = build_gridfinity_base(grid_x, grid_y)
        # Default to a solid block for complex array cutting
        self.solid = build_walls(self.base_plate, grid_x, grid_y, grid_z, is_solid=True, wall_thickness=2.0)

    def basic_storage_bin(self, **kwargs):
        logger.info("CadEngine executing: basic_storage_bin")
        if self.base_plate is None:
            self.gridfinity_base(**kwargs)
        # Replace the solid base with a hollow bin
        self.solid = build_walls(self.base_plate, self.grid_x, self.grid_y, self.grid_z, is_solid=False, wall_thickness=2.0)

    def test_tube_rack_16mm(self, **kwargs):
        logger.info("CadEngine executing: test_tube_rack_16mm")
        if self.solid is None:
            self.gridfinity_base(**kwargs)
            
        count = kwargs.get("count", 10)
        diameter = kwargs.get("diameter", 16.0)
        pitch = ConstraintSolver.calculate_pitch(diameter, 4.0)
        
        rows, cols, start_x, start_y = ConstraintSolver.calculate_array_bounds(count, pitch)
        
        pts = []
        placed = 0
        for r in range(rows):
            for c in range(cols):
                if placed >= count: break
                pts.append((start_x + c * pitch, start_y - r * pitch))
                placed += 1
                
        hole_diam = ConstraintSolver.calculate_hole_diameter(diameter, is_press_fit=False)
        GeometryValidator.validate_points_in_bounds(pts, hole_diam / 2.0, self.grid_x, self.grid_y)
        
        radius = hole_diam / 2.0
        depth = (self.grid_z * self.HEIGHT_UNIT) - 2.0
        self.solid = self.solid.faces(">Z").workplane(centerOption="CenterOfMass").pushPoints(pts).circle(radius).cutBlind(-abs(depth))

    def mx_switch_tester(self, **kwargs):
        logger.info("CadEngine executing: mx_switch_tester")
        if self.solid is None:
            self.gridfinity_base(**kwargs)
            
        # Optional: apply angled slope if requested in kwargs, default 15
        angle = kwargs.get("tilt", 15.0)
        outer_w = self.grid_x * 42.0 - 0.5
        outer_l = self.grid_y * 42.0 - 0.5
        tot_h = self.grid_z * self.HEIGHT_UNIT
        
        cutter = (
            cq.Workplane("XY")
            .workplane(offset=self.BASE_HEIGHT + tot_h) 
            .transformed(rotate=(-angle, 0, 0))
            .rect(outer_w * 3, outer_l * 3)
            .extrude(tot_h + 20)
        )
        self.solid = self.solid.cut(cutter)
        
        count = kwargs.get("count", 16)
        pitch = kwargs.get("pitch", 19.05)
        body_size = kwargs.get("body", 14.0)
        
        rows, cols, start_x, start_y = ConstraintSolver.calculate_array_bounds(count, pitch)
        
        pts = []
        placed = 0
        for r in range(rows):
            for c in range(cols):
                if placed >= count: break
                # adjust z by the slope
                pts.append((start_x + c * pitch, start_y - r * pitch))
                placed += 1
                
        GeometryValidator.validate_points_in_bounds(pts, body_size / 2.0, self.grid_x, self.grid_y)
        self.solid = self.solid.faces(">Z").workplane(centerOption="CenterOfMass").pushPoints(pts).rect(body_size, body_size).cutBlind(-6.0)

    def arduino_uno_tray(self, **kwargs):
        logger.info("CadEngine executing: arduino_uno_tray")
        if self.base_plate is None:
            self.grid_x, self.grid_y = 2, 2
            self.gridfinity_base(grid_x=self.grid_x, grid_y=self.grid_y, grid_z=self.grid_z)
        
        # Make hollow
        self.solid = build_walls(self.base_plate, self.grid_x, self.grid_y, self.grid_z, is_solid=False, wall_thickness=2.0)
        
        # Extract mounting points from kwargs if present
        pts = kwargs.get("mount_pattern", [
            [14.0, 2.5], [66.0, 7.5], [66.0, 35.5], [15.3, 50.8]
        ])
        
        # Center the Arduino footprint
        offset_x = -34.3
        offset_y = -26.7
        aligned_pts = [(p[0] + offset_x, p[1] + offset_y) for p in pts]
        
        standoffs = (
            cq.Workplane("XY")
            .workplane(offset=self.BASE_HEIGHT)
            .pushPoints(aligned_pts)
            .circle(3.0)
            .extrude(5.0)
            .faces(">Z")
            .workplane()
            .circle(1.5)
            .cutBlind(-5.0)
        )
        self.solid = self.solid.union(standoffs)

    def export_stl(self) -> bytes:
        if self.solid is None:
            raise ValueError("No solid geometry generated.")
            
        if not GeometryValidator.validate_manifold(self.solid):
            raise ValueError("Topology is broken or disjoint.")
            
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
            tmp_path = tmp.name
        
        cq.exporters.export(self.solid, tmp_path, "STL")
        
        with open(tmp_path, "rb") as f:
            stl_data = f.read()
            
        os.remove(tmp_path)
        return stl_data

    def export_glb(self) -> bytes:
        stl_bytes = self.export_stl()
        import trimesh
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp_stl:
            tmp_stl.write(stl_bytes)
            tmp_stl_path = tmp_stl.name

        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp_glb:
            tmp_glb_path = tmp_glb.name

        mesh = trimesh.load_mesh(tmp_stl_path, file_type="stl")
        
        if hasattr(mesh, 'visual'):
            mesh.visual.vertex_colors = [128, 128, 128, 255]

        mesh.export(tmp_glb_path, file_type="glb")

        with open(tmp_glb_path, "rb") as f:
            glb_data = f.read()

        os.remove(tmp_stl_path)
        os.remove(tmp_glb_path)
        return glb_data
