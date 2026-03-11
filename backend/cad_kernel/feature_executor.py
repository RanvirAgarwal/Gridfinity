import logging
from cad_kernel.feature_registry import FEATURE_REGISTRY

logger = logging.getLogger(__name__)

class FeatureExecutor:
    """
    Executes a FeatureGraph in topological order.
    Ensures that exactly ONE base tray is modified by all subsequent features.
    """
    def __init__(self):
        self.tray = None

    def execute(self, feature_graph):
        for node in feature_graph.execution_order():
            node_data = feature_graph.graph.nodes[node]
            feature_name = node_data["feature"]
            params = node_data["params"]

            if feature_name not in FEATURE_REGISTRY:
                raise ValueError(f"Feature '{feature_name}' not found in registry.")

            feature_func = FEATURE_REGISTRY[feature_name]
            logger.info(f"FeatureExecutor running: {feature_name} with params: {params}")

            if self.tray is None:
                self.tray = feature_func(**params)
            else:
                before_vol = self.tray.val().Volume()
                self.tray = feature_func(self.tray, **params)
                after_vol = self.tray.val().Volume()
                
                if abs(after_vol - before_vol) < 0.01:
                    logger.warning(f"⚠ Feature {feature_name} produced no geometry volume change!")
                
        return self.tray
