"""
Base Tool Class
All tools should inherit from this base class
"""
from typing import Dict, Any
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Base class for all MCP tools"""
    
    def __init__(self):
        self.name = self.get_name()
        self.description = self.get_description()
        self.input_schema = self.get_input_schema()
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the tool name"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the tool description"""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for input parameters"""
        pass
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format for MCP protocol"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }
