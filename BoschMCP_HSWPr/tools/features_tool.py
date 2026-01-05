from typing import Dict, Any
import logging
from .base_tool import BaseTool
from features.feature_registry import feature_registry

logger = logging.getLogger(__name__)

class FeaturesListTool(BaseTool):
    def get_name(self) -> str:
        return "features_list"

    def get_description(self) -> str:
        return "List available MCP features"

    def get_input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        features = feature_registry.list_features()
        logger.info(f"FeaturesListTool returning {len(features)} features")
        return {"features": features}

class FeatureCallTool(BaseTool):
    def get_name(self) -> str:
        return "feature_call"

    def get_description(self) -> str:
        return "Execute an MCP feature by name"

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "arguments": {"type": "object"}
            },
            "required": ["name"]
        }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not feature_registry.has_feature(name):
            raise ValueError(f"Feature '{name}' not found")
        result = feature_registry.get(name).execute(arguments)
        return {"name": name, "result": result}
