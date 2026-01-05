# Tools Directory

This directory contains all MCP tool implementations for BoschMCP_HSWPr Server.

## 📁 Structure

```
tools/
├── __init__.py           # Package initialization
├── base_tool.py         # Base class for all tools
├── tool_registry.py     # Tool registry and management
├── add_tool.py          # Add tool implementation
└── README.md            # This file
```

## 🛠️ Available Tools

### AddTool (`add`)
**File:** `add_tool.py`  
**Description:** Adds two numbers together and returns the result  
**Parameters:**
- `a` (number): First number to add
- `b` (number): Second number to add

**Returns:**
```json
{
  "result": 35.0,
  "operation": "10.0 + 25.0",
  "timestamp": "2025-12-30T12:00:00Z"
}
```

## 📝 Creating a New Tool

To add a new tool, follow these steps:

### 1. Create Tool Class

Create a new file in the `tools/` directory (e.g., `multiply_tool.py`):

```python
"""
Multiply Tool - Multiplies two numbers
"""
from typing import Dict, Any
from datetime import datetime
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class MultiplyTool(BaseTool):
    """Tool for multiplying two numbers"""
    
    def get_name(self) -> str:
        return "multiply"
    
    def get_description(self) -> str:
        return "Multiply two numbers together and return the result"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number to multiply"
                },
                "b": {
                    "type": "number",
                    "description": "Second number to multiply"
                }
            },
            "required": ["a", "b"]
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the multiply operation"""
        try:
            a = float(params.get("a"))
            b = float(params.get("b"))
            result = a * b
            
            logger.info(f"✓ Multiply operation: {a} * {b} = {result}")
            
            return {
                "result": result,
                "operation": f"{a} * {b}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            logger.error(f"✗ Multiply operation failed: {str(e)}")
            raise
```

### 2. Register the Tool

Update `tool_registry.py`:

```python
from .multiply_tool import MultiplyTool

class ToolRegistry:
    def _register_default_tools(self):
        self.register_tool(AddTool())
        self.register_tool(MultiplyTool())  # Add this line
```

### 3. Update Package Exports

Update `__init__.py`:

```python
from .add_tool import AddTool
from .multiply_tool import MultiplyTool

__all__ = ['AddTool', 'MultiplyTool']
```

### 4. Test Your Tool

Restart the server and test:

```bash
# Start server
python server.py

# Test with curl
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "multiply",
      "arguments": {"a": 5, "b": 7}
    }
  }'
```

## 🎨 BaseTool Methods

All tools inherit from `BaseTool` and must implement:

### Required Methods:

1. **`get_name() -> str`**
   - Returns the unique tool name
   - Example: `"add"`, `"multiply"`, `"search"`

2. **`get_description() -> str`**
   - Returns a clear description of what the tool does
   - Used in tool listings

3. **`get_input_schema() -> Dict[str, Any]`**
   - Returns JSON Schema for input validation
   - Defines required and optional parameters

4. **`execute(params: Dict[str, Any]) -> Dict[str, Any]`**
   - Executes the tool logic
   - Takes parameters as dictionary
   - Returns result as dictionary

### Inherited Methods:

- **`to_dict() -> Dict[str, Any]`**
  - Converts tool to MCP protocol format
  - Automatically includes name, description, and schema

## 🔍 Tool Registry API

The `ToolRegistry` class manages all tools:

### Methods:

- **`register_tool(tool: BaseTool)`** - Register a new tool
- **`get_tool(name: str) -> BaseTool`** - Get tool by name
- **`list_tools() -> List[Dict[str, Any]]`** - List all tools
- **`execute_tool(name: str, params: Dict[str, Any])`** - Execute a tool
- **`has_tool(name: str) -> bool`** - Check if tool exists
- **`get_tool_count() -> int`** - Get number of tools

### Global Instance:

```python
from tools.tool_registry import tool_registry

# The registry is automatically initialized with all default tools
tools = tool_registry.list_tools()
result = tool_registry.execute_tool("add", {"a": 10, "b": 20})
```

## 📚 Best Practices

1. **Error Handling**: Always use try-except in `execute()` method
2. **Logging**: Use logger to track operations
3. **Validation**: Validate all input parameters
4. **Type Conversion**: Handle type conversions gracefully
5. **Return Format**: Return consistent dictionary structure
6. **Documentation**: Add docstrings to all methods
7. **Testing**: Write tests for each tool

## 🧪 Testing Tools

Create test files for your tools:

```python
# test_multiply_tool.py
import pytest
from tools.multiply_tool import MultiplyTool

def test_multiply_tool():
    tool = MultiplyTool()
    result = tool.execute({"a": 5, "b": 7})
    assert result["result"] == 35
    assert "operation" in result
    assert "timestamp" in result
```

## 📦 Tool Examples

### Simple Calculation Tool
```python
class SubtractTool(BaseTool):
    def get_name(self) -> str:
        return "subtract"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        a = float(params["a"])
        b = float(params["b"])
        return {"result": a - b}
```

### String Manipulation Tool
```python
class UpperCaseTool(BaseTool):
    def get_name(self) -> str:
        return "uppercase"
    
    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert"}
            },
            "required": ["text"]
        }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        text = params["text"]
        return {"result": text.upper()}
```

### API Integration Tool
```python
class WeatherTool(BaseTool):
    def get_name(self) -> str:
        return "weather"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        city = params["city"]
        # Call weather API
        weather_data = fetch_weather(city)
        return {"result": weather_data}
```

## 🔒 Security Considerations

1. **Input Validation**: Always validate and sanitize inputs
2. **Error Messages**: Don't expose sensitive information in errors
3. **Rate Limiting**: Consider rate limiting for expensive operations
4. **Authentication**: Add authentication if needed
5. **Logging**: Log operations but not sensitive data

## 📞 Support

For questions about tool development, contact the BoschMCP_HSWPr development team.
