from typing import Dict, Any, List
from .base_feature import BaseFeature

class FeatureRegistry:
    """Registry for managing MCP features"""

    def __init__(self):
        self.features: Dict[str, BaseFeature] = {}
        self._register_default_features()

    def _register_default_features(self):
        from .failsafe_docgen import FailsafeDocGenFeature
        from .test_report_reviewer import TestReportReviewerFeature
        self.register(FailsafeDocGenFeature())
        self.register(TestReportReviewerFeature())

    def register(self, feature: BaseFeature) -> None:
        self.features[feature.name] = feature

    def get(self, name: str) -> BaseFeature:
        if name not in self.features:
            raise KeyError(f"Feature '{name}' not found")
        return self.features[name]

    def list_features(self) -> List[Dict[str, Any]]:
        return [feature.to_dict() for feature in self.features.values()]

    def has_feature(self, name: str) -> bool:
        return name in self.features

    def get_feature_count(self) -> int:
        return len(self.features)

feature_registry = FeatureRegistry()
