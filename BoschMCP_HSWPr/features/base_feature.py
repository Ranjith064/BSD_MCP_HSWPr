from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseFeature(ABC):
    """Base class for all MCP features"""

    name: str
    description: str

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the feature logic and return a result payload"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "failure_word": {
                        "type": "string", 
                        "description": "Failure word or identifier for failsafe document generation"
                    },
                    "fw_name": {
                        "type": "string",
                        "description": "Firmware name (optional, can be used as failure word)"
                    }
                },
            },
        }
