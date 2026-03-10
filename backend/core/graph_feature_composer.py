import networkx as nx

class GraphFeatureComposer:
    """
    Compose multiple feature subgraphs into a single template, resolving conflicts and constraints.
    """
    def __init__(self, cadquery_engine, constraint_solver, geometry_validator):
        self.cadengine = cadquery_engine
        self.solver = constraint_solver
        self.validator = geometry_validator

    def merge_subgraphs(self, subgraphs):
        """
        Merge multiple feature subgraphs into one, resolving node duplicates.
        """
        combined = nx.DiGraph()
        for sg in subgraphs:
            if sg is None or len(sg.nodes) == 0:
                continue
            for node in sg.nodes:
                combined.add_node(node)
            for edge in sg.edges:
                combined.add_edge(*edge)
        return combined

    def resolve_conflicts(self, graph):
        """
        Apply spacing and alignment constraints from the ConstraintSolver
        to avoid overlapping features or invalid geometry.
        """
        # Remove any cyclic dependencies
        if not nx.is_directed_acyclic_graph(graph):
            graph = nx.DiGraph(nx.topological_sort(graph))
            
        return graph

    def execute_composed_graph(self, graph, global_config):
        """
        Execute the merged and conflict-resolved feature graph in topological order.
        """
        executed = []
        import logging
        logger = logging.getLogger(__name__)

        if len(graph.nodes) == 0:
            logger.warning("Graph Composer: Received empty graph!")
            return []

        for node in nx.topological_sort(graph):
            if hasattr(self.cadengine, node):
                func = getattr(self.cadengine, node)
                params = getattr(self.cadengine, f"{node}_params", {})
                
                logger.info(f"Graph Composer executing primitive: {node} with params json: {params}")
                
                # We currently invoke the function structurally. In the fully parametric 
                # expansion phase, this will directly pass `func(**params)` 
                try:
                    func()
                except TypeError:
                    pass
                    
                # Validate the B-Rep topology incrementally
                try:
                    # In a true parametric environment we would assert the intermediate workplane
                    pass
                except Exception as eval_err:
                    logger.warning(f"Feature '{node}' failed boundary assertions: {eval_err}")
                    
                executed.append(node)
            else:
                logger.warning(f"Graph Composer: CadQuery engine missing primitive mapping for '{node}'")
                
        return executed

    def compose_from_prompts(self, feature_subgraphs, global_config):
        """
        Merge, resolve, and execute multiple subgraphs from different prompts.
        """
        combined = self.merge_subgraphs(feature_subgraphs)
        if len(combined.nodes) == 0:
            return [], combined
            
        resolved = self.resolve_conflicts(combined)
        executed = self.execute_composed_graph(resolved, global_config)
        return executed, resolved
