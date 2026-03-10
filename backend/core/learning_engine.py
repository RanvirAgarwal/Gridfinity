import json
import os
import logging
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class RecipeTracker:
    """
    Tracks every successful CAD generation as a JSON recipe.
    """
    def __init__(self, path="learning_recipes"):
        self.path = path
        os.makedirs(self.path, exist_ok=True)

    def save_recipe(self, recipe: dict):
        """
        Save a feature graph recipe after STL validation.
        """
        try:
            timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
            component = recipe.get("component") or "unknown_component"
            filename = f"{component}_{timestamp}.json"
            recipe['timestamp'] = timestamp
            
            filepath = os.path.join(self.path, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(recipe, f, indent=2)
            logger.info(f"Learning Engine: Saved successful generation recipe to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save recipe: {e}")


class PatternAnalyzer:
    """
    Analyzes the saved recipes to detect repeated feature graph patterns.
    """
    def __init__(self, path="learning_recipes"):
        self.path = path

    def discover_patterns(self, min_occurrences=5):
        """
        Returns feature graphs used at least `min_occurrences` times.
        """
        feature_graphs = []
        if not os.path.exists(self.path):
            return {}
            
        for file in os.listdir(self.path):
            if not file.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.path, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("status") == "valid":
                        # Convert feature graph to a tuple for counting
                        graph_list = data.get("feature_graph", [])
                        fg_tuple = tuple(f.get("feature") for f in graph_list if isinstance(f, dict))
                        if fg_tuple:
                            feature_graphs.append(fg_tuple)
            except Exception as e:
                logger.error(f"Failed to parse recipe {file}: {e}")

        counts = Counter(feature_graphs)
        # Only keep frequently used feature sequences
        return {fg: count for fg, count in counts.items() if count >= min_occurrences}


class TemplatePromoter:
    """
    Promotes frequently used feature graphs into the official template library.
    """
    def __init__(self, template_library="official_templates.json"):
        self.template_library = template_library
        try:
            if os.path.exists(self.template_library):
                with open(self.template_library, "r", encoding="utf-8") as f:
                    self.templates = json.load(f)
            else:
                self.templates = {}
        except Exception as e:
            logger.error(f"Failed to initialize TemplatePromoter: {e}")
            self.templates = {}

    def promote(self, feature_graph, template_name):
        """
        Add or update a template in the library.
        """
        self.templates[template_name] = {"feature_graph": feature_graph}
        try:
            # Ensure directory exists if path is nested
            os.makedirs(os.path.dirname(self.template_library) or ".", exist_ok=True)
            with open(self.template_library, "w", encoding="utf-8") as f:
                json.dump(self.templates, f, indent=2)
            logger.info(f"TemplatePromoter: Promoted {template_name} to official templates.")
        except Exception as e:
            logger.error(f"Failed to promote template {template_name}: {e}")


class LearningEngine:
    """
    Full pipeline for learning new CAD templates.
    """
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.dirname(__file__)
            
        # Place data directories alongside the backend code mapping
        self.recipe_path = os.path.join(base_dir, "..", "learning_recipes")
        self.template_library = os.path.join(base_dir, "..", "hardware_library", "learned_templates.json")
        
        self.tracker = RecipeTracker(self.recipe_path)
        self.analyzer = PatternAnalyzer(self.recipe_path)
        self.promoter = TemplatePromoter(self.template_library)

    def record_generation(self, recipe: dict):
        """
        Save a completed feature graph recipe.
        """
        self.tracker.save_recipe(recipe)

    def update_templates(self, min_occurrences=5):
        """
        Discover repeated feature graphs and promote them to official templates.
        """
        patterns = self.analyzer.discover_patterns(min_occurrences)
        for fg, count in patterns.items():
            template_name = "_".join(fg)
            self.promoter.promote(list(fg), template_name)
            logger.info(f"Learning Engine: Learned {template_name} ({count} occurrences) as a parametric template!")

    def summarize_recipes(self):
        """
        Return a summary of all valid recipes.
        """
        summary = []
        if not os.path.exists(self.tracker.path):
            return summary
            
        for file in os.listdir(self.tracker.path):
            if not file.endswith(".json"):
                continue
            with open(os.path.join(self.tracker.path, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                summary.append({
                    "prompt": data.get("prompt"),
                    "component": data.get("component"),
                    "feature_count": len(data.get("feature_graph", [])),
                    "status": data.get("status")
                })
        return summary
