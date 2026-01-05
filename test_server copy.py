"""
Test script for BoschMCP_HSWPr Server
Tests JSON-RPC 2.0 protocol compatibility
"""
import httpx
import asyncio
import json
from typing import Dict, Any


async def test_health_check():
    """Test health check endpoint"""
    print("\n" + "=" * 70)
    print("🏥 Testing Health Check")
    print("=" * 70)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False


async def test_initialize():
    """Test initialize method"""
    print("\n" + "=" * 70)
    print("🔌 Testing Initialize")
    print("=" * 70)
    
    request_data = {
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
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"\nStatus Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Verify response structure
            assert result.get("jsonrpc") == "2.0"
            assert result.get("id") == 1
            assert "result" in result
            assert result["result"]["protocolVersion"] == "2024-11-05"
            
            print("✅ Initialize test passed")
            return True
            
        except Exception as e:
            print(f"❌ Initialize test failed: {e}")
            return False


async def test_tools_list():
    """Test tools/list method"""
    print("\n" + "=" * 70)
    print("📋 Testing Tools List")
    print("=" * 70)
    
    request_data = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"\nStatus Code: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Verify response structure
            assert result.get("jsonrpc") == "2.0"
            assert result.get("id") == 2
            assert "result" in result
            assert "tools" in result["result"]
            
            tools = result["result"]["tools"]
            print(f"\n✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Tools list test failed: {e}")
            return False


async def test_add_tool():
    """Test add tool execution"""
    print("\n" + "=" * 70)
    print("➕ Testing Add Tool")
    print("=" * 70)
    
    test_cases = [
        {"a": 10, "b": 25, "expected": 35},
        {"a": -5, "b": 15, "expected": 10},
        {"a": 0.5, "b": 0.5, "expected": 1.0},
        {"a": 100, "b": -50, "expected": 50}
    ]
    
    all_passed = True
    
    async with httpx.AsyncClient() as client:
        for i, test_case in enumerate(test_cases, start=1):
            print(f"\nTest Case {i}: {test_case['a']} + {test_case['b']} = {test_case['expected']}")
            
            request_data = {
                "jsonrpc": "2.0",
                "id": 2 + i,
                "method": "tools/call",
                "params": {
                    "name": "add",
                    "arguments": {
                        "a": test_case["a"],
                        "b": test_case["b"]
                    }
                }
            }
            
            try:
                response = await client.post(
                    "http://localhost:8000/",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Verify response structure
                assert result.get("jsonrpc") == "2.0"
                assert result.get("id") == 2 + i
                assert "result" in result
                
                print(f"✅ Test Case {i} passed")
                
            except Exception as e:
                print(f"❌ Test Case {i} failed: {e}")
                all_passed = False
    
    return all_passed


async def test_invalid_method():
    """Test invalid method handling"""
    print("\n" + "=" * 70)
    print("🚫 Testing Invalid Method")
    print("=" * 70)
    
    request_data = {
        "jsonrpc": "2.0",
        "id": 999,
        "method": "invalid/method",
        "params": {}
    }
    
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            result = response.json()
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Should return error
            assert "error" in result
            assert result["error"]["code"] == -32601
            
            print("✅ Error handling test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 BoschMCP_HSWPr Server Test Suite")
    print("=" * 70)
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Health Check", await test_health_check()))
    
    if results[-1][1]:  # Only continue if server is healthy
        results.append(("Initialize", await test_initialize()))
        results.append(("Tools List", await test_tools_list()))
        results.append(("Add Tool", await test_add_tool()))
        results.append(("Invalid Method", await test_invalid_method()))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    print("\n🚀 Starting MCP Server Tests...")
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
