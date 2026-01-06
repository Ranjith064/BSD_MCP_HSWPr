"""
Tool Registry - Manages all available tools
"""
from typing import Dict, Any, List
import logging
from .base_tool import BaseTool
from .add_tool import AddTool
from .find_component_tool import FindComponentTool
from .features_tool import FeaturesListTool, FeatureCallTool
from .splitter_file_parser_tool import SplitterFileParserTool
from .code_understanding_tool import CodeUnderstandingTool
from .process_locator_tool import ProcessLocatorTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing MCP tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools"""
        # Register the add tool
        self.register_tool(AddTool())
        
        # Register the find component tool
        self.register_tool(FindComponentTool())

        # Register features tools
        self.register_tool(FeaturesListTool())
        self.register_tool(FeatureCallTool())
        # Register the splitter file parser tool
        self.register_tool(SplitterFileParserTool())
        # Register code understanding tool
        self.register_tool(CodeUnderstandingTool())
        # Register process locator tool
        self.register_tool(ProcessLocatorTool())
        # Register fetch root path tool
        from .fetch_root_path_tool import FetchRootPathTool
        self.register_tool(FetchRootPathTool())
        # Add more tools here in the future:
        # self.register_tool(SubtractTool())
        # self.register_tool(MultiplyTool())
        # etc.
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools[name]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with parameters"""
        tool = self.get_tool(name)
        return tool.execute(params)
    
    def has_tool(self, name: str) -> bool:
        """Check if a tool exists"""
        return name in self.tools
    
    def get_tool_count(self) -> int:
        """Get the number of registered tools"""
        return len(self.tools)


# Global tool registry instance
tool_registry = ToolRegistry()
