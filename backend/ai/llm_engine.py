"""
Gridfinity AI — LLM Engine (Gemini Integration)

Translates a user's natural language prompt + resolved tool dimensions
into a structured BinConfig JSON that the CadQuery engine can execute.
"""

import os
import json
import logging
from dotenv import load_dotenv

from core.schemas import BinConfig, Cutout, ProfileType
from core.tool_library import search_tools, ToolItem

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# ── Gemini client (lazy init) ────────────────────────────────────────────────

_gemini_model = None


def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — using mock fallback")
            return None
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    return _gemini_model


# ── System prompt for structured JSON output ─────────────────────────────────

SYSTEM_PROMPT = """You are a parametric CAD configuration assistant for the Gridfinity modular storage system.

GRIDFINITY RULES:
- Each grid unit is 42mm x 42mm.
- Bins are measured in grid units: grid_x (1-6) and grid_y (1-6).
- Height is measured in "height units" (grid_z, 1-12), where each unit ≈ 7mm above the 4.75mm base.
- The usable interior of a 1x1 bin is approximately 41.5mm x 41.5mm.
- The usable interior of an NxM bin is approximately (N*42 - 0.5)mm x (M*42 - 0.5)mm.
- Maximum usable depth = (grid_z * 7) mm. Cutout depth cannot exceed this.
- All cutout positions (pos_x, pos_y) are OFFSETS FROM THE CENTER of the bin interior.

YOUR TASK:
Given a user's description and a set of resolved tool dimensions, output a JSON object matching this exact schema:

{
  "grid_x": <int 1-6>,
  "grid_y": <int 1-6>,
  "grid_z": <int 1-12>,
  "label": "<short description>",
  "cutouts": [
    {
      "label": "<item name>",
      "width": <float mm>,
      "length": <float mm>,
      "depth": <float mm>,
      "pos_x": <float mm offset from center>,
      "pos_y": <float mm offset from center>,
      "profile_type": "rectangular" | "cylindrical",
      "corner_radius": <float mm, default 1.5>
    }
  ]
}

RULES:
1. Choose grid_x and grid_y large enough to fit all items with ≥1.2mm walls between them and from edges.
2. Choose grid_z tall enough so all items can be placed standing up (or lying down as appropriate).
3. Apply clearance tolerances to every dimension (already included in the provided dimensions).
4. Arrange cutouts so they don't overlap. Use a simple grid/row layout.
5. output ONLY valid JSON. No markdown, no explanation, no commentary.
"""


def _resolve_tools_from_prompt(prompt: str) -> list[ToolItem]:
    """Extract tool references from the user prompt using substring matching."""
    words = prompt.lower()
    found: list[ToolItem] = []
    seen_ids: set[str] = set()

    # Try searching for multi-word fragments
    for tool in search_tools(""):
        pass  # no-op; we'll search explicitly below

    # Check every tool against the prompt
    from tool_library import TOOL_LIBRARY
    for tool in TOOL_LIBRARY:
        if tool.id in seen_ids:
            continue
        # Check if name or any alias appears in the prompt
        if tool.name.lower() in words:
            found.append(tool)
            seen_ids.add(tool.id)
            continue
        for alias in tool.aliases:
            if alias.lower() in words:
                found.append(tool)
                seen_ids.add(tool.id)
                break
    return found


def _build_tool_context(tools: list[ToolItem]) -> str:
    """Build a human-readable context string of resolved tool dimensions."""
    if not tools:
        return "No specific tools were identified. Use the user's description to infer reasonable dimensions."
    lines = ["RESOLVED TOOL DIMENSIONS (already include clearance tolerances):"]
    for t in tools:
        tol = t.clearance_tolerance
        lines.append(
            f"- {t.name}: {t.width + tol*2:.1f}mm W × "
            f"{t.length + tol*2:.1f}mm L × {t.height + tol*2:.1f}mm H "
            f"(profile: {t.profile_type.value})"
        )
    return "\n".join(lines)


def _mock_generate(prompt: str, tools: list[ToolItem]) -> BinConfig:
    """
    Fallback when no Gemini key is available.
    Creates a simple layout automatically from resolved tools.
    """
    import math

    if not tools:
        # Default: empty 1x1 bin
        return BinConfig(grid_x=1, grid_y=1, grid_z=3, label="Empty bin")

    # Calculate needed interior space
    total_width = sum(t.width + t.clearance_tolerance * 2 for t in tools)
    max_length = max(t.length + t.clearance_tolerance * 2 for t in tools)
    max_height = max(t.height + t.clearance_tolerance * 2 for t in tools)

    # Determine grid size
    grid_x = max(1, min(6, math.ceil((total_width + 2.4) / 41.5)))
    grid_y = max(1, min(6, math.ceil((max_length + 2.4) / 41.5)))
    grid_z = max(1, min(12, math.ceil(max_height / 7.0)))

    interior_w = grid_x * 42 - 0.5
    interior_l = grid_y * 42 - 0.5

    # Simple left-to-right layout
    cutouts: list[Cutout] = []
    cursor_x = -interior_w / 2
    for t in tools:
        w = t.width + t.clearance_tolerance * 2
        l = t.length + t.clearance_tolerance * 2
        h = t.height + t.clearance_tolerance * 2

        cx = cursor_x + w / 2 + 1.2  # 1.2mm wall from left
        cy = 0.0

        cutouts.append(Cutout(
            label=t.name,
            width=round(w, 1),
            length=round(l, 1),
            depth=round(min(h, grid_z * 7), 1),
            pos_x=round(cx, 1),
            pos_y=round(cy, 1),
            profile_type=t.profile_type,
        ))
        cursor_x += w + 1.2  # 1.2mm wall between items

    return BinConfig(
        grid_x=grid_x, grid_y=grid_y, grid_z=grid_z,
        cutouts=cutouts,
        label=prompt[:60],
    )


async def generate_bin_config(prompt: str) -> BinConfig:
    """
    Main entry point: take a user prompt and return a structured BinConfig.
    Uses Gemini if available, otherwise falls back to mock generation.
    """
    import asyncio

    # Step 1: Resolve tools from prompt
    tools = _resolve_tools_from_prompt(prompt)
    logger.info(f"Resolved {len(tools)} tools from prompt: {[t.name for t in tools]}")

    # Step 2: Try Gemini
    model = _get_gemini_model()
    if model is None:
        logger.info("Using mock generator (no API key)")
        return _mock_generate(prompt, tools)

    tool_context = _build_tool_context(tools)
    user_message = f"{tool_context}\n\nUSER REQUEST: {prompt}"

    def _blocking_gemini_call():
        """Run the synchronous Gemini API call in a thread."""
        response = model.generate_content(
            [
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
                {"role": "model", "parts": [{"text": "Understood. I will output only valid JSON matching the BinConfig schema."}]},
                {"role": "user", "parts": [{"text": user_message}]},
            ]
        )
        return response.text.strip()

    try:
        # Run blocking call in thread pool with 15s timeout
        raw = await asyncio.wait_for(
            asyncio.to_thread(_blocking_gemini_call),
            timeout=15.0
        )

        # Strip possible markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        data = json.loads(raw)
        config = BinConfig(**data)
        logger.info(f"Gemini generated config: {config.grid_x}x{config.grid_y}x{config.grid_z} with {len(config.cutouts)} cutouts")
        return config

    except asyncio.TimeoutError:
        logger.warning("Gemini API timed out (15s). Using mock fallback.")
        return _mock_generate(prompt, tools)
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}. Falling back to mock.")
        return _mock_generate(prompt, tools)

