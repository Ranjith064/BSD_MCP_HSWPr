"""
Test FindComponent Tool via JSON-RPC
"""
import httpx
import asyncio
import json


async def test_find_component_via_jsonrpc():
    """Test FindComponent tool through the MCP server"""
    
    print("=" * 70)
    print("🧪 Testing FindComponent Tool via JSON-RPC")
    print("=" * 70)
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        # Test 1: List tools to verify find_component is registered
        print("\n📋 Test 1: List all tools")
        list_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        try:
            response = await client.post("http://localhost:8000/", json=list_request)
            result = response.json()
            tools = result.get("result", {}).get("tools", [])
            
            print(f"Available tools: {[t['name'] for t in tools]}")
            
            find_component_tool = next((t for t in tools if t['name'] == 'find_component'), None)
            if find_component_tool:
                print("✅ find_component tool is registered")
                print(f"   Description: {find_component_tool['description']}")
            else:
                print("❌ find_component tool NOT found")
                return
                
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return
        
        # Test 2: Find component 'rbwss'
        print("\n🔍 Test 2: Find component 'rbwss'")
        call_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "find_component",
                "arguments": {
                    "keyword": "rbwss"
                }
            }
        }
        
        try:
            response = await client.post("http://localhost:8000/", json=call_request)
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if "result" in result:
                print("✅ Test 2 PASSED")
            else:
                print("❌ Test 2 FAILED")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Find component 'rbrfp'
        print("\n🔍 Test 3: Find component 'rbrfp'")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "find_component",
                "arguments": {
                    "keyword": "rbrfp"
                }
            }
        }
        
        try:
            response = await client.post("http://localhost:8000/", json=call_request)
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if "result" in result:
                print("✅ Test 3 PASSED")
            else:
                print("❌ Test 3 FAILED")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Invalid keyword
        print("\n🔍 Test 4: Invalid keyword 'xyz'")
        call_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "find_component",
                "arguments": {
                    "keyword": "xyz"
                }
            }
        }
        
        try:
            response = await client.post("http://localhost:8000/", json=call_request)
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if "result" in result:
                print("✅ Test 4 PASSED (correctly handled invalid keyword)")
            else:
                print("❌ Test 4 FAILED")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ All JSON-RPC tests complete")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_find_component_via_jsonrpc())
