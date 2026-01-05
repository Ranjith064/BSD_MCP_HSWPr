#!/usr/bin/env python3
"""
Quick test to verify tools and features are working
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'BoschMCP_HSWPr'))

try:
    from tools.tool_registry import tool_registry
    from features.feature_registry import feature_registry
    
    print("=== Tools Registry ===")
    tools = tool_registry.list_tools()
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")
    
    print(f"\nTotal tools: {len(tools)}")
    
    print("\n=== Features Registry ===")
    features = feature_registry.list_features()
    for feature in features:
        print(f"- {feature['name']}: {feature['description']}")
        
    print(f"\nTotal features: {len(features)}")
    
    print("\n=== Test Features List Tool ===")
    if tool_registry.has_tool('features_list'):
        result = tool_registry.execute_tool('features_list', {})
        print(f"Features list result: {result}")
    else:
        print("❌ features_list tool not found!")
    
    print("\n=== Test Feature Call Tool ===")
    if tool_registry.has_tool('feature_call'):
        result = tool_registry.execute_tool('feature_call', {
            'name': 'FailsafeDocGen', 
            'arguments': {}
        })
        print(f"Feature call result: {result}")
    else:
        print("❌ feature_call tool not found!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()