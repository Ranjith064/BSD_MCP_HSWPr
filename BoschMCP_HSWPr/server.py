"""
BoschMCP_HSWPr Server
FastAPI-based MCP server compatible with BSD Client
Uses JSON-RPC 2.0 protocol over HTTP
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import time
import logging
import uvicorn
from datetime import datetime
from tools.tool_registry import tool_registry
from features.feature_registry import feature_registry
from controllers.hswpr_controller import controller as hswpr_controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="BoschMCP_HSWPr Server",
    description="MCP server compatible with BSD Client - JSON-RPC 2.0",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Pydantic Models
# ============================================

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[int, str]
    method: str
    params: Optional[Dict[str, Any]] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[int, str]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

# ============================================
# JSON-RPC Method Handlers
# ============================================

def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request"""
    logger.info("🔌 Client initializing connection")
    
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "BoschMCP_HSWPr",
            "version": "1.0.0"
        }
    }

def handle_tools_list(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle tools/list request"""
    tools = tool_registry.list_tools()
    logger.info(f"📋 Listed {len(tools)} available tools")
    return {"tools": tools}

def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request"""
    tool_name = params.get("name")
    tool_params = params.get("arguments", {})
    
    logger.info(f"🔧 Calling tool: {tool_name} with params: {tool_params}")
    
    if not tool_registry.has_tool(tool_name):
        raise ValueError(f"Tool '{tool_name}' not found")
    
    # Execute tool using registry
    result = tool_registry.execute_tool(tool_name, tool_params)
    
    return {
        "content": [
            {
                "type": "text",
                "text": str(result)
            }
        ]
    }

def handle_features_list(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    features = feature_registry.list_features()
    logger.info(f"📋 Listed {len(features)} available features")
    return {"features": features}

def handle_features_call(params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})
    logger.info(f"✨ Calling feature: {name} with params: {arguments}")
    if not feature_registry.has_feature(name):
        raise ValueError(f"Feature '{name}' not found")
    result = feature_registry.get(name).execute(arguments)
    return {
        "content": [
            {"type": "text", "text": str(result)}
        ]
    }

# JSON-RPC method router
JSONRPC_METHODS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
    "features/list": handle_features_list,
    "features/call": handle_features_call
}

# ============================================
# Endpoints
# ============================================

@app.post("/")
async def jsonrpc_handler(request: Request):
    """Main JSON-RPC 2.0 endpoint"""
    try:
        body = await request.json()
        
        # Validate JSON-RPC request
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request - jsonrpc must be '2.0'"
                    }
                }
            )
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        logger.info(f"📨 JSON-RPC Request: method={method}, id={request_id}")
        
        # Route to appropriate handler
        if method not in JSONRPC_METHODS:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )
        
        # Execute method
        try:
            result = JSONRPC_METHODS[method](params)
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            logger.info(f"✅ JSON-RPC Response: id={request_id}, success=True")
            return JSONResponse(content=response)
            
        except Exception as e:
            logger.error(f"❌ Method execution error: {str(e)}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
            )
    
    except Exception as e:
        logger.error(f"❌ Request processing error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                }
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "server": "BoschMCP_HSWPr",
        "protocol": "JSON-RPC 2.0",
        "tools_count": tool_registry.get_tool_count(),
        "tools": [tool["name"] for tool in tool_registry.list_tools()],
        "features_count": feature_registry.get_feature_count(),
        "features": [feature["name"] for feature in feature_registry.list_features()],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "name": "BoschMCP_HSWPr Server",
        "version": "1.0.0",
        "protocol": "JSON-RPC 2.0 over HTTP",
        "description": "MCP server compatible with BSD Client",
        "endpoints": {
            "jsonrpc": "POST /",
            "health": "GET /health",
            "docs": "GET /docs"
        },
        "tools": [tool["name"] for tool in tool_registry.list_tools()],
        "features": [feature["name"] for feature in feature_registry.list_features()]
    }

# ============================================
# Startup
# ============================================

if __name__ == "__main__":
    import os
    
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    logger.info("=" * 70)
    logger.info(f"🚀 Starting BoschMCP_HSWPr Server")
    logger.info("=" * 70)
    logger.info(f"📍 Host: {host}")
    logger.info(f"🔌 Port: {port}")
    logger.info(f"🛠️  Tools: {[tool['name'] for tool in tool_registry.list_tools()]}")
    logger.info(f"📡 Protocol: JSON-RPC 2.0 over HTTP")
    logger.info("=" * 70)
    logger.info(f"🌐 Server URL: http://{host}:{port}")
    logger.info(f"❤️  Health Check: http://{host}:{port}/health")
    logger.info(f"📚 API Docs: http://{host}:{port}/docs")
    logger.info("=" * 70)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
