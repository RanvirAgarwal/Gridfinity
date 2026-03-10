"""
Pydantic models for the Gridfinity AI API.
All request/response schemas live here.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ── Tool Library Models ──────────────────────────────────────────────────────

class ProfileType(str, Enum):
    RECTANGULAR = "rectangular"
    CYLINDRICAL = "cylindrical"


class ToolItem(BaseModel):
    """A single item in the Tool Library with verified physical dimensions."""
    id: str
    name: str
    aliases: list[str] = []
    category: str
    width: float = Field(..., description="X-axis dimension in mm")
    length: float = Field(..., description="Y-axis dimension in mm")
    height: float = Field(..., description="Z-axis dimension in mm")
    clearance_tolerance: float = Field(
        default=0.5, description="Extra clearance per side in mm for slip fit"
    )
    profile_type: ProfileType = ProfileType.RECTANGULAR


# ── CadQuery Generation Models ──────────────────────────────────────────────

class Cutout(BaseModel):
    """A single pocket/cutout to be subtracted from the bin interior."""
    label: str = ""
    width: float = Field(..., description="X dimension in mm (including tolerance)")
    length: float = Field(..., description="Y dimension in mm (including tolerance)")
    depth: float = Field(..., description="Z depth in mm")
    pos_x: float = Field(default=0.0, description="X center offset from bin center in mm")
    pos_y: float = Field(default=0.0, description="Y center offset from bin center in mm")
    profile_type: ProfileType = ProfileType.RECTANGULAR
    corner_radius: float = Field(default=1.5, description="Fillet radius for rectangular pockets")


class BinConfig(BaseModel):
    """
    The structured 5-Layer configuration output by the LLM.
    Fully describes a Gridfinity bin to be generated.
    """
    grid_x: int = Field(default=1, ge=1, description="Grid units in X (each 42mm)")
    grid_y: int = Field(default=1, ge=1, description="Grid units in Y (each 42mm)")
    grid_z: int = Field(default=3, ge=1, description="Height units (each ~7mm above the base)")
    
    # Hardcoded Template Routing
    template_name: str = Field(
        default="basic_storage_bin", 
        description="The explicit predefined template to use for generation."
    )
    
    # Legacy fields kept for frontend compatibility but ignored by backend geometry engine
    structure: Optional[str] = Field(default="hollow_bin", description="Either 'solid_block' or 'hollow_bin'")
    operations: Optional[list] = Field(default_factory=list, description="Array of Boolean actions (ignored in v2)")


# ── API Request / Response ───────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Natural language description of the desired Gridfinity bin",
    )


class GuardrailWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"  # warning | error


class GenerateResponse(BaseModel):
    success: bool
    config: Optional[BinConfig] = None
    stl_url: Optional[str] = None
    glb_url: Optional[str] = None
    warnings: list[GuardrailWarning] = []
    error: Optional[str] = None
