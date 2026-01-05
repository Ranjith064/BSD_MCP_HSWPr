# BoschMCP_HSWPr Server

A FastAPI-based MCP (Model Context Protocol) server compatible with BSD Client.

## 🎯 Features

- **Protocol**: JSON-RPC 2.0 over HTTP
- **Framework**: FastAPI
- **Transport**: HTTP
- **Compatible**: BSD Client v2.0

## 🛠️ Available Tools

### `add`
Adds two numbers together and returns the result.

**Parameters:**
- `a` (number): First number to add
- `b` (number): Second number to add

**Example:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "add",
    "arguments": {
      "a": 10,
      "b": 25
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{'result': 35, 'operation': '10.0 + 25.0', 'timestamp': '2025-12-23T10:00:00Z'}"
      }
    ]
  }
}
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd BoschMCP_HSWPr
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python server.py
```

The server will start on `http://127.0.0.1:8000`

### 3. Test the Server

**Health Check:**
```bash
curl http://localhost:8000/health
```

**JSON-RPC Request:**
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

## 📡 Endpoints

### JSON-RPC Endpoint
- **URL**: `POST /`
- **Purpose**: Main JSON-RPC 2.0 endpoint for all MCP methods

### Health Check
- **URL**: `GET /health`
- **Purpose**: Server health status

### Root Info
- **URL**: `GET /`
- **Purpose**: Server information and available endpoints

### API Documentation
- **URL**: `GET /docs`
- **Purpose**: Interactive Swagger UI documentation

## 🔌 BSD Client Integration

### Configuration

Add to your BSD Client's `config/config.yaml`:

```yaml
mcp:
  servers:
    bosch_hswpr:
      name: "BoschMCP_HSWPr Server"
      description: "MCP server with add functionality"
      url: "http://localhost:8000"
      enabled: true
      auto_connect: true
      timeout: 30
      capabilities:
        - "tools"
```

### Usage in BSD Client

```bash
# Start BSD Client
python src/main.py

# Use the add tool
RJC5KOR > @add 10 25

# Or via MCP command
RJC5KOR > /mcp invoke bosch_hswpr add {"a": 10, "b": 25}
```

## 🧪 Testing

### Python Test Script

```python
import httpx
import asyncio
import json

async def test_mcp_server():
    async with httpx.AsyncClient() as client:
        # Test initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "Test Client",
                    "version": "1.0.0"
                }
            }
        }
        response = await client.post("http://localhost:8000/", json=init_request)
        print("Initialize:", response.json())
        
        # Test tools/list
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        response = await client.post("http://localhost:8000/", json=list_request)
        print("Tools List:", response.json())
        
        # Test tools/call (add)
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {
                    "a": 15,
                    "b": 27
                }
            }
        }
        response = await client.post("http://localhost:8000/", json=call_request)
        print("Add Result:", response.json())

# Run test
asyncio.run(test_mcp_server())
```

## 🔧 Environment Variables

- `MCP_HOST`: Server host (default: `127.0.0.1`)
- `MCP_PORT`: Server port (default: `8000`)

## 📝 JSON-RPC Methods

### `initialize`
Initialize MCP session

**Params:**
- `protocolVersion`: Protocol version (e.g., "2024-11-05")
- `capabilities`: Client capabilities
- `clientInfo`: Client name and version

### `tools/list`
List all available tools

**Params:** None or empty object

### `tools/call`
Call a specific tool

**Params:**
- `name`: Tool name (e.g., "add")
- `arguments`: Tool parameters as object

## 🛡️ Error Codes

- `-32700`: Parse error
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

## 📚 Adding More Tools

To add a new tool:

1. **Add to TOOLS_REGISTRY:**
```python
TOOLS_REGISTRY["my_tool"] = {
    "name": "my_tool",
    "description": "Tool description",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."}
        },
        "required": ["param1"]
    }
}
```

2. **Create handler function:**
```python
def handle_my_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    param1 = params.get("param1")
    # Your logic here
    return {"result": "..."}
```

3. **Register handler:**
```python
TOOL_HANDLERS["my_tool"] = handle_my_tool
```

## 🐳 Docker Support (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
```

Build and run:
```bash
docker build -t bosch-mcp-hswpr .
docker run -p 8000:8000 bosch-mcp-hswpr
```

## 📞 Support

For issues or questions, contact the BSD Client development team.

## 📄 License

Bosch Internal Use Only
