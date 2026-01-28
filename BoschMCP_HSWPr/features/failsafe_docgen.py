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

        # Step 1: Execute find_component tool with the failure word
        # (Client LLM should call find_component and use its output)
        prompt = (
            f"Step 1: Ensure the failure word is provided by the user.\n"
            f"Step 2: Call the 'find_component' tool with the failure word to get the component path.\n"
            f"Step 3: Use the returned component path as the search root. Remove the prefix 'FW_' from the failure word if present, then use the search tool to recursively search all files (of any type) in all subfolders within the component path for:\n"
            f"  - the normalized failure word as a substring\n"
            f"  - related identifiers such as 'DemConf_DemEventParameter_<failure_word>' (where <failure_word> is the normalized failure word)\n"
            f"Remember the list of files found for all these patterns.\n"
            f"Step 4: Call the splitter file handler tool (splitter_file_parser) with the failure word and component path.\n"
            f"Step 5: For each relevant function or process name found in the search step, call the 'code_understanding' tool with the function name, failure word, and component path to extract code snippets and analyze the monitoring logic.\n"
            f"Return the results of steps 3, 4, and 5 to the user."
        )
        return {
            "status": "plan_ready",
            "failure_word": failure_word.strip(),
            "prompt": prompt
        }
