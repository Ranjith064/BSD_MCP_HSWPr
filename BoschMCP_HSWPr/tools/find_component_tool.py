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
    
    def _search_failure_word_in_txt(self, root_path: str, failure_word: str):
        """
        Search for the failure word in all .txt files under the root folder.
        Returns the first matching file path, or None if not found.
        """
        import os
        matches = []
        for dirpath, _, filenames in os.walk(root_path):
            for fname in filenames:
                if fname.lower().endswith('.txt'):
                    fpath = os.path.join(dirpath, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line in f:
                                if failure_word in line:
                                    matches.append(fpath)
                                    break
                    except Exception:
                        continue
        return matches[0] if matches else None
    
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
                    "description": "Failure word to search for in .txt files."
                },
                "project_root": {
                    "type": "string",
                    "description": "Absolute path to the root folder to search."
                }
            },
            "required": ["failure_word", "project_root"]
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for the failure word in .txt files and generate the component name from the path."""
        try:
            failure_word = params.get("failure_word")
            project_root = params.get("project_root")
            if not failure_word or not isinstance(failure_word, str) or failure_word.strip() == "":
                raise ValueError("Parameter 'failure_word' is required and cannot be empty")
            if not project_root or not isinstance(project_root, str) or project_root.strip() == "":
                raise ValueError("Parameter 'project_root' is required and cannot be empty")

            failure_word = failure_word.strip()
            project_root = project_root.strip()

            # Step 1: Search for the failure word in all .txt files under the root folder
            match_path = self._search_failure_word_in_txt(project_root, failure_word)
            if not match_path:
                return {
                    "found": False,
                    "failure_word": failure_word,
                    "component_name": None,
                    "message": f"Failure word '{failure_word}' not found in any .txt file under {project_root}.",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

            # Step 2: Generate the component name based on the path (e.g., use the parent folder name)
            import os
            component_name = os.path.basename(os.path.dirname(match_path))

            return {
                "found": True,
                "failure_word": failure_word,
                "component_name": component_name,
                "file_path": match_path,
                "message": f"Component '{component_name}' found for failure word '{failure_word}' in file: {match_path}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            logger.error(f"✗ FindComponent operation failed: {str(e)}")
            raise
