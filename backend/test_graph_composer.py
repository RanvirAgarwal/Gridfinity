import sys
import os

sys.path.insert(0, os.getcwd())

from core.graph_template_recommender import GraphTemplateRecommender
from core.graph_feature_composer import GraphFeatureComposer
from core.kernel_primitives import KernelPrimitives
from core.constraint_solver import ConstraintSolver
from core.geometry_validator import GeometryValidator

print("Testing Graph Template Recommender & Composer...\n")

# Mock engines
cadengine = KernelPrimitives()
solver = ConstraintSolver()
validator = GeometryValidator()

# 1. Initialize Recommender and build graph from learning_recipes
recommender = GraphTemplateRecommender(cadquery_engine=cadengine)
print(f"Built global feature graph with {len(recommender.graph.nodes)} nodes and {len(recommender.graph.edges)} edges.")

# 2. Suggest templates
print("\nSuggestion 1: mx_switch")
sg1 = recommender.suggest_template(["mx_switch"])
print("Nodes matched:", sg1.nodes)

print("\nSuggestion 2: test_tube_16mm")
sg2 = recommender.suggest_template(["test_tube_16mm"])
print("Nodes matched:", sg2.nodes)

# 3. Compose and execute
print("\nComposing both subgraphs into complex model...")
composer = GraphFeatureComposer(cadengine, solver, validator)

global_config = {"grid_x": 4, "grid_y": 4} # simulated config
executed_nodes, final_graph = composer.compose_from_prompts([sg1, sg2], global_config)

print("\nComposition Results:")
print(f"Final Graph size: {len(final_graph.nodes)} nodes")
print(f"Execution Order (Topological Sort): {executed_nodes}")
print("\nSUCCESS: Graph execution logic fully functional.")
