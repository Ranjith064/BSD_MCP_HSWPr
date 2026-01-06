from typing import Dict, Any
from .base_tool import BaseTool

class FetchRootPathTool(BaseTool):
    name = "fetch_root_path"
    description = (
        "Step 1: Prompt the user to enter the Project Root path. Do NOT assume, infer, or auto-fill the path. "
        "Step 2: Receive the path from the Client LLM to MCP."
    )

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_root": {
                    "type": "string",
                    "description": "Absolute path to the root of your project."
                }
            },
            "required": []
        }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Step 1: Prompt the user for the project root path if not provided. Do NOT assume, infer, or auto-fill the path.
        project_root = (params or {}).get("project_root")
        if not project_root or not isinstance(project_root, str) or project_root.strip() == "":
            return {
                "status": "input_required",
                "request_type": "project_root",
                "message": "Step 1: Please enter the absolute path to your project root folder. Do NOT assume, infer, or auto-fill the path. Only proceed after the user provides this input.",
                "prompt": "Enter project root folder path:"
            }

        # Step 2: Receive the path from Client LLM to MCP and use it in your workflow
        def example_receive_project_root_path(path: str):
            """
            Example function to receive and use the project root path from Client LLM to MCP.
            Args:
                path (str): Absolute path to the project root provided by the user.
            Returns:
                str: Confirmation message.
            """
            # Here you would use the path in your workflow
            return f"Project root path received: {path}"

        confirmation = example_receive_project_root_path(project_root)

        return {
            "status": "ok",
            "project_root": project_root,
            "confirmation": confirmation,
            "instructions": (
                "Step 1: Prompt the user to enter the Project Root path. Do NOT assume, infer, or auto-fill the path.\n"
                "Step 2: Receive the path from Client LLM to MCP and use it in your workflow."
            ),
            "example_function": (
                "def example_receive_project_root_path(path: str):\n"
                "    # Use the provided path in your workflow\n"
                "    return f'Project root path received: {path}'\n"
            )
        }
