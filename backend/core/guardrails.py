"""
Layer 2 Auxiliary: Legacy Guardrail Handlers

Active topological constraints (like clamping wall depth and bounds) are now 
mechanically enforced by the centralized constraint_engine.py. 
This file remains to format warnings back to the Frontend UI.
"""

import logging
from core.schemas import BinConfig, GuardrailWarning

logger = logging.getLogger(__name__)

def validate_config(config: BinConfig) -> list[GuardrailWarning]:
    """
    Checks for LLM fallback status or decode failures to display UI toasters.
    """
    warnings: list[GuardrailWarning] = []
    
    operations = getattr(config, "operations", []) if getattr(config, "operations", None) else []
    for op in operations:
        op_type = op.get("type", "")
        if op_type == "connection_error_fallback":
            warnings.append(GuardrailWarning(
                code="LLM_OFFLINE",
                message="Local Ollama daemon is dead. Safe hollow_bin fallback generated.",
                severity="warning"
            ))
            break
        elif op_type == "decode_error_fallback":
            warnings.append(GuardrailWarning(
                code="LLM_DECODE",
                message="Local Ollama generated invalid JSON. Safe hollow_bin fallback generated.",
                severity="warning"
            ))
            break

    return warnings
