import os
import json
import logging
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize AsyncOpenAI with the Local Ollama base URL
client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama", # Required by the client but ignored by the local daemon
)

# ── Schemas ──────────────────────────────────────────────────────────────────

class AdvancedGenerateRequest(BaseModel):
    prompt: str = Field(..., description="User's natural language request")

class AdvancedGenerateResponse(BaseModel):
    success: bool
    structure: Optional[str] = None
    grid_x: Optional[int] = None
    grid_y: Optional[int] = None
    base_height: Optional[int] = None
    template_name: Optional[str] = None
    components: Optional[list] = None
    item_count: Optional[int] = None
    component_id: Optional[str] = None
    operations: Optional[list] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None

SYSTEM_PROMPT = """You are a CAD generation system using CadQuery for the Gridfinity architecture.
Your ONLY job is to read the user's prompt, select the most appropriate hardcoded template, and output the required grid parameters.

CRITICAL ENGINEERING CONSTANTS:
You MUST only use component dimensions from the provided component library.
Never guess measurements.
All geometry must be in millimeters.
Gridfinity base unit = 42mm.
Gridfinity height unit = 7mm.
Minimum wall thickness = 2mm.
Clearance for inserts = 0.4mm.
All arrays must exactly match the requested quantity.

The ONLY allowed values for 'template_name' are:
- "basic_storage_bin"
- "test_tube_rack_16mm"
- "arduino_uno_tray"
- "mx_switch_tester"
- "metric_screw_organizer"
- "angled_ring_display"
- "hex_mesh_sterilization_tray"

If the user's request doesn't clearly match a specific template, fallback to "basic_storage_bin".
If the user specifies hardware elements, you must extract ALL of them into the 'components' array.
For each hardware component mentioned, if it exists in the COMPONENT LIBRARY DATA provided below, add an object with its exact 'id' and the requested 'count' (default to 1 if not specified).

OUTPUT SPECIFICATION:
You MUST output EXACTLY one JSON object containing ONLY grid_x, grid_y, template_name, and components.
{
  "grid_x": int,
  "grid_y": int,
  "template_name": str,
  "components": [
    {"id": str, "count": int}
  ] // Empty array if no components specified
}
"""

# ── Endpoint ─────────────────────────────────────────────────────────────────

LOCAL_MODEL = "qwen2.5-coder:7b"

@router.post("/api/generate_advanced", response_model=AdvancedGenerateResponse)
async def generate_advanced(req: AdvancedGenerateRequest):
    """
    Advanced routing LLM endpoint for processing structural Gridfinity requirements
    using a local Ollama instance to bypass rate limits.
    """
    logger.info(f"Local Ollama routing logic triggered for prompt: '{req.prompt}'")
    
    try:
        logger.info(f"Attempting inference with local model: {LOCAL_MODEL}")
        # Load and intelligently filter component library dynamically
        lib_path = os.path.join(os.path.dirname(__file__), "..", "hardware_library", "engineering_library.json")
        try:
            with open(lib_path, "r", encoding="utf-8") as f:
                full_lib = json.load(f)
                
            # Filter the massive 500+ component library to avoid overloading the LLM context window
            prompt_lower = req.prompt.lower()
            filtered_lib = {}
            for comp_id, comp_data in full_lib.items():
                category = comp_data.get("category", "").lower()
                # Simple keyword matching heuristic
                if (comp_id.replace("_", " ") in prompt_lower or 
                    category.replace("_", " ") in prompt_lower or
                    "board" in prompt_lower and category == "electronics_board" or
                    "switch" in prompt_lower and category == "keyboard_switch" or
                    "screw" in prompt_lower and category == "fastener"):
                    filtered_lib[comp_id] = comp_data
            
            # If extremely sparse, fallback to a small generic selection to prevent empty library
            if not filtered_lib and len(full_lib) > 0:
                 # Provide 10 generic samples from the dictionary
                 filtered_lib = dict(list(full_lib.items())[:10])
                 
            lib_data = json.dumps(filtered_lib, indent=2)
            logger.info(f"Dynamically filtered {len(full_lib)} library components down to {len(filtered_lib)} relevant subsets for prompt inclusion.")
        except Exception as e:
            logger.error(f"Failed to load engineering library: {e}")
            lib_data = "No custom library loaded."

        full_prompt = SYSTEM_PROMPT + f"\n\nCOMPONENT LIBRARY DATA:\n{lib_data}"

        response = await client.chat.completions.create(
            model=LOCAL_MODEL,
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": req.prompt}
            ],
            temperature=0.0  # Zero temperature for deterministic strict JSON compliance
        )
        
        raw_text = response.choices[0].message.content.strip()
        logger.info(f"Ollama Raw Response: {raw_text}")
        
        # Clean arbitrary markdown fencing to prevent decoding crashes
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        elif raw_text.startswith("```json"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        
        raw_text = raw_text.strip()
        
        # Safe JSON parse with explicit try/except fallback mechanisms
        try:
            data = json.loads(raw_text)
            return AdvancedGenerateResponse(
                success=True,
                structure="hollow_bin",
                grid_x=data.get("grid_x", 1),
                grid_y=data.get("grid_y", 1),
                base_height=6,
                template_name=data.get("template_name", "basic_storage_bin"),
                components=data.get("components", []),
                item_count=data.get("item_count"),
                component_id=data.get("component_id"),
                operations=[],
                raw_response=raw_text
            )
            
        except json.JSONDecodeError as je:
            logger.error(f"Failed to decode Ollama JSON: {raw_text}")
            return AdvancedGenerateResponse(
                success=True,
                structure="hollow_bin",
                grid_x=1,
                grid_y=1,
                base_height=6,
                template_name="basic_storage_bin",
                components=[],
                item_count=None,
                component_id=None,
                operations=[{"type": "decode_error_fallback", "error": str(je)}],
                raw_response=raw_text
            )

    except Exception as e:
        logger.exception("Ollama API request failed")
        # Ensure generation continues by returning a safe physical mock fallback 
        # instead of breaking the entire app pipeline upon connection errors (e.g. Ollama not running).
        return AdvancedGenerateResponse(
            success=True,
            structure="hollow_bin",
            grid_x=1,
            grid_y=1,
            base_height=6,
            template_name="basic_storage_bin",
            components=[],
            item_count=None,
            component_id=None,
            operations=[{"type": "connection_error_fallback", "error": str(e)}],
            raw_response=f"Fallback active: Local daemon failed. Ensure Ollama is running. {str(e)}"
        )
