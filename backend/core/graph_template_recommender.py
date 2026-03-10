import json
import os
import networkx as nx

class GraphTemplateRecommender:
    """
    Builds a feature graph from learning recipes and recommends/composes templates.
    """

    def __init__(self, recipe_path=None, cadquery_engine=None):
        if recipe_path is None:
            recipe_path = os.path.join(os.path.dirname(__file__), "..", "learning_recipes")
        self.recipe_path = recipe_path
        self.cadengine = cadquery_engine
        self.graph = self.build_feature_graph_db()

    def build_feature_graph_db(self):
        """
        Construct a directed graph of all features from valid recipes.
        """
        G = nx.DiGraph()
        if not os.path.exists(self.recipe_path):
            return G
            
        for file in os.listdir(self.recipe_path):
            if not file.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.recipe_path, file), "r", encoding="utf-8") as f:
                    recipe = json.load(f)
                    if recipe.get("status") != "valid":
                        continue
                    # Parse feature_graph structure
                    feature_nodes = recipe.get("feature_graph", [])
                    nodes = [f.get("feature") for f in feature_nodes if isinstance(f, dict)]
                    if not nodes:
                        continue
                        
                    edges = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
                    G.add_nodes_from(nodes)
                    G.add_edges_from(edges)
            except Exception as e:
                print(f"Failed to parse {file}: {e}")
        return G

    def suggest_template(self, prompt_keywords):
        """
        Returns a subgraph containing nodes that match the prompt keywords.
        """
        expanded_tokens = []
        for k in set(prompt_keywords):
            expanded_tokens.extend(k.lower().replace("-", "_").split("_"))
            
        # Remove empty or tiny tokens
        expanded_tokens = [t for t in expanded_tokens if len(t) > 1]
        
        sub_nodes = []
        for n in self.graph.nodes:
            n_lower = str(n).lower()
            # Heuristic: the feature node name must contain at least one of the component ID tokens
            if any(t in n_lower for t in expanded_tokens):
                sub_nodes.append(n)
                
        # Include immediate dependencies (predecessors) so the subgraph is complete
        # e.g. if 'mx_switch_tester' matches, we probably need 'gridfinity_base' before it
        extended_nodes = set(sub_nodes)
        for n in sub_nodes:
            extended_nodes.update(nx.ancestors(self.graph, n))
            
        subgraph = self.graph.subgraph(list(extended_nodes)).copy()
        return subgraph

    def execute_feature_graph(self, subgraph=None):
        """
        Execute CadQuery kernel primitives in topological order.
        """
        if subgraph is None:
            subgraph = self.graph
        executed_features = []
        for node in nx.topological_sort(subgraph):
            if hasattr(self.cadengine, node):
                func = getattr(self.cadengine, node)
                func()
                executed_features.append(node)
            else:
                print(f"Warning: CadQuery engine missing primitive '{node}'")
        return executed_features

    def compose_from_prompt(self, prompt, min_nodes=1):
        """
        Automatically compose a feature graph from a user prompt.
        Returns executed nodes and subgraph.
        """
        keywords = prompt.lower().split()
        subgraph = self.suggest_template(keywords)
        if len(subgraph.nodes) < min_nodes:
            print("No sufficient matching feature graph found; using default template.")
            return [], None
        executed = self.execute_feature_graph(subgraph)
        return executed, subgraph

    def save_graph_db(self, filename="feature_graph_db.json"):
        """
        Serialize the feature graph to JSON for visualization or reuse.
        """
        data = {
            "nodes": list(self.graph.nodes),
            "edges": list(self.graph.edges)
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
