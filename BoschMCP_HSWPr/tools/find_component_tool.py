"""
FindComponent Tool - Finds component names based on keywords
"""
from typing import Dict, Any
from datetime import datetime
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class FindComponentTool(BaseTool):
    """Tool for finding component names based on keywords"""
    
    def _lookup_failure_word_metadata(self, failure_word: str):
        """
        Look up the failure word in metadata/failure_word_map.json and return component name and file path.
        """
        import os
        import json
        metadata_path = os.path.join(os.path.dirname(__file__), '../../metadata/failure_word_map.json')
        metadata_path = os.path.normpath(metadata_path)
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data:
            if entry.get('failure_word') == failure_word:
                # Support both 'component_path' and 'file_path' keys
                component_name = entry.get('component_name')
                file_path = entry.get('component_path') or entry.get('file_path')
                return component_name, file_path
        return None, None
    
    def get_name(self) -> str:
        return "find_component"
    
    def get_description(self) -> str:
        return "Find component name based on keyword. Supports keywords: rbwss (Wheel Speed Sensor), rbrfp (Return Flow Pump - DC motor)"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "failure_word": {
                    "type": "string",
                    "description": "Failure word to look up in metadata file."
                }
            },
            "required": ["failure_word"]
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Look up the failure word in metadata and return component name and merged file path."""
        try:
            failure_word = params.get("failure_word")
            project_root = params.get("project_root")
            if not failure_word or not isinstance(failure_word, str) or failure_word.strip() == "":
                raise ValueError("Parameter 'failure_word' is required and cannot be empty")
            failure_word = failure_word.strip()
            component_name, component_path = self._lookup_failure_word_metadata(failure_word)
            if not component_name or not component_path:
                return {
                    "found": False,
                    "failure_word": failure_word,
                    "component_name": None,
                    "file_path": None,
                    "message": f"Failure word '{failure_word}' not found in metadata file.",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            # Merge project_root and component_path if project_root is provided
            import os
            if project_root and isinstance(project_root, str) and project_root.strip():
                merged_path = os.path.normpath(os.path.join(project_root.strip(), *component_path.replace('Project root folder', '').lstrip('/\\').split('/')))
            else:
                merged_path = component_path
            return {
                "found": True,
                "failure_word": failure_word,
                "component_name": component_name,
                "file_path": merged_path,
                "message": f"Component '{component_name}' found for failure word '{failure_word}' in file: {merged_path}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            logger.error(f"✗ FindComponent operation failed: {str(e)}")
            raise
