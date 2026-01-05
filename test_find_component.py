"""
Test script for FindComponent Tool
"""
import sys
sys.path.insert(0, r'C:\BoschSoftwareDeveloper\Project_01\BSD_Client\BoschMCP_HSWPr')

from tools.find_component_tool import FindComponentTool

print("=" * 70)
print("🧪 Testing FindComponent Tool")
print("=" * 70)

tool = FindComponentTool()

print(f"\n📋 Tool Info:")
print(f"   Name: {tool.name}")
print(f"   Description: {tool.description}")

# Test cases
test_cases = [
    {"keyword": "rbwss", "expected": "Wheel Speed Sensor"},
    {"keyword": "rbrfp", "expected": "Return Flow Pump - DC motor"},
    {"keyword": "RBWSS", "expected": "Wheel Speed Sensor"},  # Test case-insensitive
    {"keyword": "invalid", "expected": None},  # Test not found
]

print("\n" + "=" * 70)
print("🧪 Running Test Cases")
print("=" * 70)

for i, test_case in enumerate(test_cases, start=1):
    keyword = test_case["keyword"]
    expected = test_case["expected"]
    
    print(f"\nTest Case {i}: keyword='{keyword}'")
    
    try:
        result = tool.execute({"keyword": keyword})
        
        print(f"   Found: {result['found']}")
        print(f"   Component: {result.get('component_name', 'N/A')}")
        print(f"   Message: {result['message']}")
        
        if result['found'] and result['component_name'] == expected:
            print(f"   ✅ PASSED")
        elif not result['found'] and expected is None:
            print(f"   ✅ PASSED (correctly not found)")
            print(f"   Available keywords: {result.get('available_keywords', [])}")
        else:
            print(f"   ❌ FAILED - Expected: {expected}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 70)
print("✅ FindComponent Tool Testing Complete")
print("=" * 70)
