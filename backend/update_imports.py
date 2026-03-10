import os
import re

root_dir = r"c:\Users\ranvi\project\backend"

replacements = [
    (r"from schemas import", r"from core.schemas import"),
    (r"from tool_library import", r"from core.tool_library import"),
    (r"from llm_engine import", r"from ai.llm_engine import"),
    (r"from cadquery_engine import", r"from core.cadquery_engine import"),
    (r"from guardrails import", r"from core.guardrails import"),
    (r"from export import", r"from pipeline.export import"),
    (r"from constraint_engine import", r"from core.constraint_engine import"),
    (r"import database", r"from components import database"),
    (r"from database import", r"from components.database import"),
    (r"import openrouter_engine", r"from ai import openrouter_engine")
]

for root, dirs, files in os.walk(root_dir):
    if 'venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements:
                new_content = re.sub(r"^" + old, new, new_content, flags=re.MULTILINE)
            
            # Special case for openrouter_engine import in main.py
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path}")
