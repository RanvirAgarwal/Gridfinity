import networkx as nx

class FeatureGraph:
    """
    Dependency graph for CAD features.
    Ensures safe execution order where all components modify the same root body.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_feature(self, node_id, feature_name=None, params=None):
        if params is None:
            params = {}
        if feature_name is None:
            feature_name = node_id
            
        self.graph.add_node(node_id, feature=feature_name, params=params)

    def add_dependency(self, before, after):
        self.graph.add_edge(before, after)

    def execution_order(self):
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Feature graph contains cycles!")
        return list(nx.topological_sort(self.graph))
