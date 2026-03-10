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
from core.learning_engine import LearningEngine
from core.graph_template_recommender import GraphTemplateRecommender
from core.graph_feature_composer import GraphFeatureComposer
from core.kernel_primitives import KernelPrimitives
from core.constraint_solver import ConstraintSolver
from core.geometry_validator import GeometryValidator

# Initialize the self-improving CAD engine globally
learning_engine = LearningEngine()
graph_recommender = GraphTemplateRecommender()
graph_composer = GraphFeatureComposer(
    cadquery_engine=KernelPrimitives(),
    constraint_solver=ConstraintSolver(),
    geometry_validator=GeometryValidator()
)

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
        from core.schemas import BinConfig, ComponentRequest
        
        extracted_components = []
        for c in getattr(ar, "components", []) or []:
            if isinstance(c, dict) and "id" in c:
                extracted_components.append(ComponentRequest(id=c["id"], count=c.get("count", 1)))

        config = BinConfig(
            grid_x=ar.grid_x or 1,
            grid_y=ar.grid_y or 1,
            grid_z=3, # standard tray height baseline
            label=req.prompt[:60],
            template_name=getattr(ar, "template_name", "basic_storage_bin"),
            components=extracted_components,
            item_count=extracted_components[0].count if extracted_components else getattr(ar, "item_count", None),
            component_id=extracted_components[0].id if extracted_components else getattr(ar, "component_id", None)
        )
        logger.info(f"LLM extracted components: {[c.model_dump() for c in config.components]}")
        logger.info(f"Config: {config.grid_x}x{config.grid_y}x{config.grid_z}, Template: {config.template_name}, Components: {len(config.components)}")

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

        # Step 3: Failproof Multi-Feature Graph Composition & Generation
        stl_bytes = None
        glb_bytes = None
        recipe_feature_graph = []
        
        if len(config.components) >= 1:
            logger.info("Routing components to Failproof Component Pipeline for topological synthesis.")
            
            # Load engineering library to inject physical dimensions into the execution parameters
            import json, networkx as nx
            from core.cad_engine import CadEngine
            
            lib_path = os.path.join(os.path.dirname(__file__), "..", "hardware_library", "engineering_library.json")
            with open(lib_path, "r", encoding="utf-8") as f:
                component_library = json.load(f)

            subgraphs = []
            component_node_map = {}
            cadengine = CadEngine()
            
            try:
                for comp in config.components:
                    # Explicit ID lookup first
                    sg = graph_recommender.suggest_template([comp.id])
                    
                    # Fallback to token matching
                    if not sg or len(sg.nodes) == 0:
                        sg = graph_recommender.suggest_template(comp.id.replace("_", " ").split())
                        
                    if sg is not None and len(sg.nodes) > 0:
                        subgraphs.append(sg)
                        component_node_map[comp.id] = list(sg.nodes)
                
                if not subgraphs:
                    raise RuntimeError("No valid subgraphs found for any components in the dataset.")
                
                # Merge subgraphs into one DAG
                merged_graph = dict() 
                merged_graph_dag = nx.DiGraph()
                for sg in subgraphs:
                    merged_graph_dag.add_nodes_from(sg.nodes)
                    merged_graph_dag.add_edges_from(sg.edges)
                
                # Ensure DAG (remove cycles if any)
                if not nx.is_directed_acyclic_graph(merged_graph_dag):
                    merged_graph_dag = nx.DiGraph(nx.topological_sort(merged_graph_dag))
                
                # Inject parameters for each node natively
                for comp in config.components:
                    if comp.id not in component_node_map:
                        continue
                    for node in component_node_map[comp.id]:
                        params = component_library.get(comp.id, {})
                        setattr(cadengine, f"{node}_params", {**params, "count": comp.count, "grid_x": config.grid_x, "grid_y": config.grid_y})
                
                # Ensure gridfinity_base executes first inherently by setting attributes on the base plate
                if not hasattr(cadengine, "gridfinity_base_params"):
                    setattr(cadengine, "gridfinity_base_params", {"grid_x": config.grid_x, "grid_y": config.grid_y, "grid_z": config.grid_z})

                # Execute merged graph topologically with Hard Stops
                for node in nx.topological_sort(merged_graph_dag):
                    func = getattr(cadengine, node, None)
                    if func is None:
                        raise ValueError(f"Missing CAD kernel primitive for node: {node}")
                    
                    params = getattr(cadengine, f"{node}_params", {})
                    logger.info(f"Composer Engine invoking primitive: {node} ({params})")
                    func(**params)
                    
                    # Optional: Explicit validations after each step can catch overlapping cut corruption early
                    GeometryValidator.validate_manifold(cadengine.solid)
                    
                stl_bytes = cadengine.export_stl()
                glb_bytes = cadengine.export_glb()
                
                # Track executed nodes correctly
                recipe_feature_graph = [
                    {"feature": n, "params": getattr(cadengine, f"{n}_params", {})} 
                    for n in merged_graph_dag.nodes
                ]
                
            except Exception as graph_err:
                logger.error(f"Failproof topological execution crashed: {graph_err}. Falling back to default solid generator.")
                import traceback
                traceback.print_exc()
                
                stl_bytes = generate_stl(config)
                glb_bytes = generate_glb(config)
                recipe_feature_graph = [
                    {"feature": "gridfinity_base", "params": {"grid_x": config.grid_x, "grid_y": config.grid_y}},
                    {"feature": config.template_name, "params": {}}
                ]
        else:
            stl_bytes = generate_stl(config)
            glb_bytes = generate_glb(config)
            recipe_feature_graph = [
                {"feature": "gridfinity_base", "params": {"grid_x": config.grid_x, "grid_y": config.grid_y}},
                {"feature": config.template_name, "params": {}}
            ]

        if not stl_bytes or not glb_bytes:
             return GenerateResponse(
                 success=False,
                 error="Geometry generation failed. The requested dimensions or pattern may be too complex for the CAD kernel."
             )

        # Step 4: Save & return URLs
        stl_filename = save_stl(stl_bytes)
        glb_filename = save_glb(glb_bytes)

        recipe = {
            "prompt": req.prompt,
            "components": [c.model_dump() for c in config.components] if getattr(config, "components", []) else [],
            "component": config.component_id or "multi_component",
            "count": config.item_count,
            "template": config.template_name,
            "feature_graph": recipe_feature_graph,
            "status": "valid"
        }
        
        try:
            learning_engine.record_generation(recipe)
            # Evaluate pattern thresholds on every 5 valid prompts transparently
            learning_engine.update_templates(min_occurrences=5)
        except Exception as le:
            logger.error(f"Learning Engine encountered a non-fatal tracking error: {le}")

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
