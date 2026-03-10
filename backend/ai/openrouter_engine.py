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
    operations: Optional[list] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None

# ── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an intent classification AI for a Gridfinity CAD generator.
Your ONLY job is to read the user's prompt and select the most appropriate hardcoded template. 
DO NOT guess dimensions or generate any custom structures.

The ONLY allowed values for 'template_name' are:
- "basic_storage_bin"
- "test_tube_rack_16mm"
- "arduino_uno_tray"
- "mx_switch_tester"
- "metric_screw_organizer"
- "angled_ring_display"
- "hex_mesh_sterilization_tray"

If the user's request doesn't clearly match a specific template, fallback to "basic_storage_bin".

OUTPUT SPECIFICATION:
You MUST output EXACTLY one JSON object containing ONLY grid_x, grid_y, and template_name.
{
  "grid_x": int,
  "grid_y": int,
  "template_name": str
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
        response = await client.chat.completions.create(
            model=LOCAL_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
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
            operations=[{"type": "connection_error_fallback", "error": str(e)}],
            raw_response=f"Fallback active: Local daemon failed. Ensure Ollama is running. {str(e)}"
        )
