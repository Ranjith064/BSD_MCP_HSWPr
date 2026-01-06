from typing import Dict, Any
from .base_feature import BaseFeature


class FailsafeDocGenFeature(BaseFeature):
    name = "FailsafeDocGen"
    description = "Failsafe document generation workflow - returns execution plan for client LLM"

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = params or {}
        failure_word = params.get("failure_word") or params.get("fw_name")
        if not failure_word or not isinstance(failure_word, str) or failure_word.strip() == "":
            return {
                "status": "input_required",
                "request_type": "failure_word",
                "message": "Please provide the failure word to proceed.",
                "prompt": "Enter failure word:"
            }

        project_root = params.get("project_root")
        if not project_root or not isinstance(project_root, str) or project_root.strip() == "":
            return {
                "status": "input_required",
                "request_type": "project_root",
                "message": "Project root path is required. Please call the 'fetch_root_path' tool to prompt the user for the absolute path to the project root folder.",
                "prompt": "Call the 'fetch_root_path' tool and ask the user: Enter project root folder path:"
            }

        prompt = (
            f"Step 1: Ensure the failure word is provided by the user.\n"
            f"Step 2: Ensure the project root path is provided by the user.\n"
            f"Step 3: Remove the prefix 'FW_' from the failure word if present, then use the search tool to recursively search all files (of any type) in all subfolders within the project root for:\n"
            f"  - the normalized failure word as a substring\n"
            f"  - related identifiers such as 'DemConf_DemEventParameter_<failure_word>' (where <failure_word> is the normalized failure word)\n"
            f"Remember the list of files found for all these patterns.\n"
            f"Step 4: Call the splitter file handler tool (splitter_file_parser) with the failure word and project root.\n"
            f"Return the results of steps 3 and 4 to the user."
        )
        return {
            "status": "plan_ready",
            "failure_word": failure_word.strip(),
            "project_root": project_root.strip(),
            "prompt": prompt
        }
