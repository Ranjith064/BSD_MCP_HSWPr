"""Quick test to verify tools module is working"""
import sys
sys.path.insert(0, r'C:\BoschSoftwareDeveloper\Project_01\BSD_Client\BoschMCP_HSWPr')

from tools.tool_registry import tool_registry

print("✅ Tools module loaded successfully")
print(f"📋 Registered tools: {[t['name'] for t in tool_registry.list_tools()]}")
print(f"🔢 Tool count: {tool_registry.get_tool_count()}")

# Test add tool
print("\n🧪 Testing add tool:")
result = tool_registry.execute_tool("add", {"a": 10, "b": 25})
print(f"Result: {result}")
