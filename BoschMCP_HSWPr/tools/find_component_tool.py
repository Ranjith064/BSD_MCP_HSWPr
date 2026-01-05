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
    
    # Component mapping dictionary
    COMPONENT_MAP = {
        "rbwss": "Wheel Speed Sensor",
        "rbrfp": "Return Flow Pump - DC motor"
    }
    
    def get_name(self) -> str:
        return "find_component"
    
    def get_description(self) -> str:
        return "Find component name based on keyword. Supports keywords: rbwss (Wheel Speed Sensor), rbrfp (Return Flow Pump - DC motor)"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Component keyword to search for (e.g., 'rbwss', 'rbrfp')"
                }
            },
            "required": ["keyword"]
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the find component operation"""
        try:
            keyword = params.get("keyword")
            
            # Validate required parameter
            if keyword is None or keyword == "":
                raise ValueError("Parameter 'keyword' is required and cannot be empty")
            
            # Convert to lowercase for case-insensitive matching
            keyword_lower = str(keyword).lower().strip()
            
            # Search for component
            if keyword_lower in self.COMPONENT_MAP:
                component_name = self.COMPONENT_MAP[keyword_lower]
                
                logger.info(f"✓ Found component: {keyword} -> {component_name}")
                
                return {
                    "found": True,
                    "keyword": keyword,
                    "component_name": component_name,
                    "message": f"Component found: {component_name}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                logger.info(f"⚠️  Component not found for keyword: {keyword}")
                
                # Get available keywords for helpful error message
                available_keywords = list(self.COMPONENT_MAP.keys())
                
                return {
                    "found": False,
                    "keyword": keyword,
                    "component_name": None,
                    "message": f"Component not found for keyword '{keyword}'",
                    "available_keywords": available_keywords,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
        except Exception as e:
            logger.error(f"✗ FindComponent operation failed: {str(e)}")
            raise
