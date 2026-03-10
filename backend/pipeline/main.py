"""
Gridfinity AI — FastAPI Application Entry Point

Main server with CORS, static file serving for generated meshes,
and all API route registrations.
"""

import os
import sys
from pathlib import Path

# Add backend root to sys.path so modules like 'core', 'ai', 'components' resolve seamlessly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from core.schemas import GenerateRequest, GenerateResponse
from core.tool_library import search_tools, get_all_tools
from ai.llm_engine import generate_bin_config
from core.cadquery_engine import generate_stl, generate_glb
from core.guardrails import validate_config
from pipeline.export import save_stl, save_glb, GENERATED_DIR
from ai import openrouter_engine

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Gridfinity AI",
    description="Parametric Gridfinity bin generator powered by AI",
    version="0.1.0",
)

# CORS — allow the Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated files
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# Include the advanced OpenRouter API module
app.include_router(openrouter_engine.router)


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "engine": "cadquery" if _has_cq() else "fallback"}


def _has_cq():
    try:
        import cadquery
        return True
    except ImportError:
        return False


# ── Tool Library Endpoints ───────────────────────────────────────────────────

@app.get("/api/tools")
async def list_tools():
    """List all tools in the library."""
    return [t.model_dump() for t in get_all_tools()]


@app.get("/api/tools/search")
async def search_tools_endpoint(q: str = ""):
    """Search the tool library by name/alias."""
    results = search_tools(q)
    return [t.model_dump() for t in results]


# ── Generation Endpoint ─────────────────────────────────────────────────────

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    """
    Main generation pipeline:
    1. LLM extracts parameters from the prompt
    2. Guardrails validate the configuration
    3. CadQuery generates the geometry
    4. STL + GLB are exported and URLs returned
    """
    try:
        # Step 1: LLM parameter extraction via Qwen3 OpenRouter
        logger.info(f"Routing logic via OpenRouter for prompt: {req.prompt[:80]}...")
        from ai.openrouter_engine import generate_advanced, AdvancedGenerateRequest
        ar = await generate_advanced(AdvancedGenerateRequest(prompt=req.prompt))
        
        if not ar.success:
            return GenerateResponse(success=False, error=ar.error)

        # Build overarching BinConfig from Qwen's JSON structural extraction
        from core.schemas import BinConfig
        config = BinConfig(
            grid_x=ar.grid_x or 1,
            grid_y=ar.grid_y or 1,
            grid_z=3, # standard tray height baseline
            label=req.prompt[:60],
            template_name=getattr(ar, "template_name", "basic_storage_bin"),
            item_count=getattr(ar, "item_count", None),
            component_id=getattr(ar, "component_id", None)
        )
        logger.info(f"Config: {config.grid_x}x{config.grid_y}x{config.grid_z}, Template: {config.template_name}")

        # Step 2: Guardrail validation
        warnings = validate_config(config)
        for w in warnings:
            logger.warning(f"Guardrail [{w.code}]: {w.message}")

        # Check for hard errors
        errors = [w for w in warnings if w.severity == "error"]
        if errors:
            return GenerateResponse(
                success=False,
                config=config,
                warnings=warnings,
                error="Configuration failed guardrail checks. See warnings.",
            )

        # Step 3: Generate geometry
        stl_bytes = generate_stl(config)
        glb_bytes = generate_glb(config)

        if not stl_bytes or not glb_bytes:
             return GenerateResponse(
                 success=False,
                 error="Geometry generation failed. The requested dimensions or pattern may be too complex for the CAD kernel."
             )

        # Step 4: Save & return URLs
        stl_filename = save_stl(stl_bytes)
        glb_filename = save_glb(glb_bytes)

        return GenerateResponse(
            success=True,
            config=config,
            stl_url=f"/generated/{stl_filename}",
            glb_url=f"/generated/{glb_filename}",
            warnings=warnings,
        )

    except Exception as e:
        logger.exception("Generation failed")
        import traceback
        with open("last_crash.txt", "w") as f:
            f.write(traceback.format_exc())
            f.write(f"\nVariables at crash: stl_bytes_type={type(stl_bytes) if 'stl_bytes' in locals() else 'Missing'}, glb_bytes_type={type(glb_bytes) if 'glb_bytes' in locals() else 'Missing'}")
        
        return GenerateResponse(
            success=False,
            error=f"Generation failed: {str(e)}",
        )


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
