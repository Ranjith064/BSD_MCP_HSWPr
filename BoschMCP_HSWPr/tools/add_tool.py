"""
Add Tool - Adds two numbers together
"""
from typing import Dict, Any
from datetime import datetime
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class AddTool(BaseTool):
    """Tool for adding two numbers"""
    
    def get_name(self) -> str:
        return "add"
    
    def get_description(self) -> str:
        return "Add two numbers together and return the result"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number to add"
                },
                "b": {
                    "type": "number",
                    "description": "Second number to add"
                }
            },
            "required": ["a", "b"]
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the add operation"""
        try:
            a = params.get("a")
            b = params.get("b")
            
            # Validate required parameters
            if a is None or b is None:
                raise ValueError("Both 'a' and 'b' parameters are required")
            
            # Convert to numbers if they're strings
            try:
                a = float(a)
                b = float(b)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Parameters 'a' and 'b' must be numbers: {str(e)}")
            
            # Perform addition
            result = a + b
            
            logger.info(f"✓ Add operation: {a} + {b} = {result}")
            
            return {
                "result": result,
                "operation": f"{a} + {b}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"✗ Add operation failed: {str(e)}")
            raise
