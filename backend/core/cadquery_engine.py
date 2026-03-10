"""
Layer 5: STL Generation Pipeline (The Builder)

This is the CAD Kernel Engine.
It takes a strictly constrained JSON specification, applies the ConstraintEngine
engineering tolerances, and composites verified `cad_templates/` modules into a robust 3D B-Rep.
"""

import os
import io
import tempfile
import logging
import cadquery as cq
import trimesh
from typing import Optional

from core.constraint_engine import ConstraintEngine
from components import database
from core.schemas import BinConfig
import json

# Features & Geometry
from core.constraint_solver import ConstraintSolver
from core.geometry_validator import GeometryValidator
from core.kernel_primitives import KernelPrimitives
from features.base import build_gridfinity_base, build_walls
from features.pcb_mount import build_pcb_mount
from core.feature_compiler import FeatureCompiler

logger = logging.getLogger(__name__)

# Replicate core system offsets for the router
BASE_HEIGHT = 4.75 
LIP_HEIGHT = 4.0
HEIGHT_UNIT = ConstraintEngine.HEIGHT_STEP

def _cq_build_bin(raw_config: BinConfig) -> cq.Workplane:
    """
    The unified master pipeline using the Hardcoded Template Architecture.
    """
    config = raw_config

    template_name = getattr(config, "template_name", "basic_storage_bin")
    
    item_count = getattr(config, "item_count", None)
    component_id = getattr(config, "component_id", None)
    
    # Load physical component dataset dynamically
    comp_data = {}
    if component_id:
        lib_path = os.path.join(os.path.dirname(__file__), "..", "hardware_library", "engineering_library.json")
        try:
            with open(lib_path, "r", encoding="utf-8") as f:
                lib = json.load(f)
                comp_data = lib.get(component_id, {})
                logger.info(f"Loaded component traits for '{component_id}': {comp_data}")
        except Exception as e:
            logger.error(f"Failed to load component library data internally: {e}")
    
    # Enforce strict geometric constraints per template to prevent kernel timeouts & disjoint rendering
    if template_name == "arduino_uno_tray":
        grid_x, grid_y = 2, 2 # Uno board size is fixed; lock grid explicitly.
    elif template_name == "hex_mesh_sterilization_tray":
        grid_x = max(1, min(config.grid_x, 3))
        grid_y = max(1, min(config.grid_y, 3)) # Cap hex mesh gen logic loop limits 
    elif template_name == "mx_switch_tester":
        slots = item_count if item_count and item_count > 0 else 16
        pitch = comp_data.get("pitch", 19.05) if comp_data else 19.05
        auto_grid_x, auto_grid_y = ConstraintSolver.compute_grid_dimensions(slots, pitch)
        grid_x = max(auto_grid_x, min(config.grid_x, 4))
        grid_y = max(auto_grid_y, min(config.grid_y, 4))
    elif template_name == "angled_ring_display":
        grid_x = max(1, min(config.grid_x, 4))
        grid_y = max(1, min(config.grid_y, 4))
    elif template_name == "test_tube_rack_16mm":
        slots = item_count if item_count and item_count > 0 else 10
        diameter = comp_data.get("diameter", 16.0) if comp_data else 16.0
        pitch = ConstraintSolver.calculate_pitch(diameter, 4.0)
        auto_grid_x, auto_grid_y = ConstraintSolver.compute_grid_dimensions(slots, pitch)
        grid_x = max(auto_grid_x, min(config.grid_x, 4))
        grid_y = max(auto_grid_y, min(config.grid_y, 4))
    else:
        grid_x = max(1, min(config.grid_x, 6))
        grid_y = max(1, min(config.grid_y, 6))
    
    # 1. Generate standard parametric Gridfinity base
    base_plate = build_gridfinity_base(grid_x, grid_y)
    
    # Base params
    grid_z = config.grid_z
    wall_thickness = 2.0
    wall_height = grid_z * HEIGHT_UNIT

    if template_name == "basic_storage_bin":
        solid = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=False, wall_thickness=wall_thickness)

    elif template_name == "test_tube_rack_16mm":
        solid = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=True, wall_thickness=wall_thickness)
        slots = item_count if item_count and item_count > 0 else 10
        diameter = comp_data.get("diameter", 16.0) if comp_data else 16.0
        pitch = ConstraintSolver.calculate_pitch(diameter, 4.0)
        
        rows, cols, start_x, start_y = ConstraintSolver.calculate_array_bounds(slots, pitch)
        
        pts = []
        placed = 0
        for r in range(rows):
            for c in range(cols):
                if placed >= slots: break
                pts.append((start_x + c * pitch, start_y - r * pitch))
                placed += 1
        
        hole_diam = ConstraintSolver.calculate_hole_diameter(diameter, is_press_fit=False)
        GeometryValidator.validate_points_in_bounds(pts, hole_diam / 2.0, grid_x, grid_y)
        solid = KernelPrimitives.circular_array_cut(solid, pts, hole_diam, (wall_height - 2.0))

    elif template_name == "arduino_uno_tray":
        solid = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=False, wall_thickness=wall_thickness)
        
        # Arduino Uno explicit offsets
        offset_x = -34.3
        offset_y = -26.7
        pts = [
            (14.0 + offset_x, 2.5 + offset_y),
            (66.0 + offset_x, 7.5 + offset_y),
            (66.0 + offset_x, 35.5 + offset_y),
            (15.3 + offset_x, 50.8 + offset_y),
        ]
        standoffs = (
            cq.Workplane("XY")
            .workplane(offset=BASE_HEIGHT)
            .pushPoints(pts)
            .circle(3.0)
            .extrude(5.0)
            .faces(">Z")
            .workplane()
            .circle(1.5)
            .cutBlind(-5.0)
        )
        solid = solid.union(standoffs)
        
        # USB explicit side wall cut
        usb_cut = (
            cq.Workplane("XZ")
            .workplane(offset=grid_y * 42.0 / 2.0)
            .center(-20, BASE_HEIGHT + 5.0)
            .rect(15, 12)
            .extrude(10, both=True)
        )
        solid = solid.cut(usb_cut)

    elif template_name == "mx_switch_tester":
        solid = KernelPrimitives.create_solid_block(base_plate, grid_x, grid_y, grid_z)
        solid = KernelPrimitives.apply_angled_cut(solid, grid_x, grid_y, grid_z, 15.0)

        slots = item_count if item_count and item_count > 0 else 16
        pitch = comp_data.get("pitch", 19.05) if comp_data else 19.05
        body_size = comp_data.get("body", 14.0) if comp_data else 14.0
        
        rows, cols, start_x, start_y = ConstraintSolver.calculate_array_bounds(slots, pitch)

        try:
            pts = []
            placed = 0
            for r in range(rows):
                for c in range(cols):
                    if placed >= slots: break
                    pts.append((start_x + c * pitch, start_y - r * pitch))
                    placed += 1
            
            GeometryValidator.validate_points_in_bounds(pts, body_size / 2.0, grid_x, grid_y)
            solid = KernelPrimitives.rectangular_array_cut(solid, pts, body_size, body_size, 6.0)
        except Exception as e:
            logger.error(f"Kernel crash during array cut for mx_switch_tester: {e}")

    elif template_name == "metric_screw_organizer":
        solid = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=False, wall_thickness=wall_thickness)
        solid = KernelPrimitives.add_divider_wall(solid, grid_y, grid_z)

    elif template_name == "angled_ring_display":
        solid = KernelPrimitives.create_solid_block(base_plate, grid_x, grid_y, grid_z)
        solid = KernelPrimitives.apply_angled_cut(solid, grid_x, grid_y, grid_z, 20.0)
        
        count_y = grid_y * 3
        
        # Use simple library diameter proxy if jewelry_ring matched
        ring_diam = comp_data.get("diameter", 22.0) if comp_data else 22.0
        slot_width = ring_diam + 3.0
        
        try:
            solid = solid.faces(">Z").workplane(centerOption="CenterOfMass").rarray(30, 10, grid_x, count_y).rect(slot_width, 3).cutBlind(-15.0)
        except Exception as e:
            logger.error(f"Kernel crash during array cut for angled_ring_display: {e}")

    elif template_name == "hex_mesh_sterilization_tray":
        solid = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=False, wall_thickness=wall_thickness)
        
        import math
        hex_radius = 4.0
        spacing = 1.5
        dx = hex_radius * 3 + spacing
        dy = hex_radius * math.sqrt(3) + spacing
        cx = int((grid_x * 42.0 - 4.0) / dx)
        cy = int((grid_y * 42.0 - 4.0) / dy)
        
        pts = []
        for i in range(cx):
            for j in range(cy):
                x = (i - cx / 2.0) * dx
                y = (j - cy / 2.0) * dy
                if i % 2 != 0:
                    y += dy / 2.0
                pts.append((x, y))
                
        hex_cut_tools = (
            cq.Workplane("XY")
            .workplane(offset=BASE_HEIGHT - 1.0) # Start slightly below floor
            .pushPoints(pts)
            .polygon(6, hex_radius * 2)
            .extrude(5.0) # Extrude through the 2mm floor
        )
        solid = solid.cut(hex_cut_tools)

    else:
        # Fallback
        solid = build_walls(base_plate, grid_x, grid_y, grid_z, is_solid=False, wall_thickness=wall_thickness)

    return solid


def generate_stl(config: BinConfig) -> Optional[bytes]:
    """Generates the geometry utilizing the 5-layer B-Rep builder pipeline."""
    logger.info(f"Generating CAD mesh from JSON definition...")
    try:
        model = _cq_build_bin(config)
        
        # Validates manifold integrity immediately before compilation logic
        if not GeometryValidator.validate_manifold(model):
            logger.error("Rejecting export: Topologically invalid or disjoint object.")
            return None
            
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
            tmp_path = tmp.name
        
        cq.exporters.export(model, tmp_path, "STL")
        
        with open(tmp_path, "rb") as f:
            stl_data = f.read()
            
        os.remove(tmp_path)
        return stl_data
        
    except Exception as e:
        logger.exception(f"Failed to generate CadQuery STL: {e}")
        return None


def generate_glb(config: BinConfig) -> Optional[bytes]:
    """Coverts the pipeline mesh to browser-ready WebGL GLB."""
    stl_bytes = generate_stl(config)
    if not stl_bytes:
        return None

    try:
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
    except Exception as e:
        logger.exception(f"Failed to convert STL to GLB: {e}")
        return None
