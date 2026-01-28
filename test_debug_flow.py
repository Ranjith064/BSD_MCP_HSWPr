"""
Debug test for RBMESG patterns that are failing
"""
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from BoschMCP_HSWPr.tools.flowchart_rules import flowchart_rules

def test_debug_flow():
    """Test the specific failing RBMESG patterns"""
    
    print("=" * 60)
    print("Debug Test for RBMESG Patterns")
    print("=" * 60)
    
    # These are the exact statements from the problematic flow chart
    failing_cases = [
        "RcvMESG(&l_MESG_BlaAct_u16, RBMESG_BlaAct_u16);",
        "RBMESG_SendMESG(RBMESG_BlaAvailableHSW_B, TRUE);", 
        "RBMESG_RcvMESG(&l_VehicleCfg_ST, RBMESG_VehicleCfg_ST);",
        "RBMESG_SendMESG(RBMESG_BlaActFiltered_B, l_BlaOutput_B);",
        "RBMICSYS_WritePort(RB_PortId_HSWPr_BlaOut_HSR_B, l_BlaOutput_B);"
    ]
}
"""

def escape_mermaid(text):
    text = text.strip()
    if '(' in text and ')' in text:
        func_match = re.search(r'(\w+)\s*\(', text)
        if func_match:
            return func_match.group(1)
    text = text.replace('"', "'")
    text = re.sub(r'[^\w\s=<>!+\-*/\[\].]', '', text)
    if len(text) > 30:
        text = text[:27] + "..."
    return text

func_lines = simple_test.strip().split('\n')
current_nodes = ["start"]
if_stack = []
brace_depth = 0
found_func_start = False

i = 0
while i < len(func_lines):
    line = func_lines[i]
    stripped = line.strip()
    
    if not found_func_start:
        if '{' in stripped:
            found_func_start = True
            brace_depth = 1
            print(f"Line {i}: Found function start, brace_depth = {brace_depth}")
        i += 1
        continue
    
    if not stripped or stripped.startswith('//'):
        i += 1
        continue
    
    # Track brace depth changes
    old_depth = brace_depth
    brace_depth += stripped.count('{') - stripped.count('}')
    print(f"Line {i}: '{stripped[:40]}' | old_depth={old_depth}, new_depth={brace_depth}")
    
    # Check if we're closing an if-else block
    if brace_depth < old_depth and if_stack:
        print(f"  -> Depth decreased! Checking if_stack: {if_stack}")
        for if_info in if_stack:
            print(f"     if_id={if_info['if_id']}, brace_depth_at_if={if_info['brace_depth_at_if']}, has_else={if_info['has_else']}, else_depth={if_info['else_depth']}")
            print(f"     yes_ends={if_info['yes_ends']}, no_ends={if_info['no_ends']}")
            print(f"     current_nodes={current_nodes}")
            
            if brace_depth <= if_info['brace_depth_at_if']:
                print(f"     -> Block should close! (brace_depth {brace_depth} <= if depth {if_info['brace_depth_at_if']})")
                if if_info['has_else'] and if_info['else_depth'] > 0 and brace_depth < if_info['else_depth']:
                    print(f"     -> Saving no_ends = {current_nodes} (brace_depth {brace_depth} < else_depth {if_info['else_depth']})")
                else:
                    print(f"     -> NOT saving no_ends (has_else={if_info['has_else']}, else_depth={if_info['else_depth']}, brace_depth={brace_depth})")
    
    # If statement
    if re.match(r'if\s*\(', stripped):
        condition = re.sub(r'if\s*\((.*)\).*', r'\1', stripped)
        if_id = f"if{len(if_stack)+1}"
        if_info = {
            'if_id': if_id,
            'brace_depth_at_if': brace_depth,
            'yes_ends': [],
            'no_ends': [],
            'has_else': False,
            'else_depth': -1
        }
        if_stack.append(if_info)
        current_nodes = [if_id + "_yes_marker"]
        print(f"  -> IF statement: {condition}, brace_depth_at_if={brace_depth}")
        i += 1
        continue
    
    # Else statement
    if re.match(r'else\s*($|\{)', stripped):
        if if_stack:
            if_info = if_stack[-1]
            if_info['has_else'] = True
            if_info['else_depth'] = brace_depth + 1  # FIXED: always one level deeper
            if_info['yes_ends'] = current_nodes[:]
            current_nodes = [if_info['if_id'] + "_no_marker"]
            print(f"  -> ELSE statement: yes_ends={if_info['yes_ends']}, else_depth={if_info['else_depth']} (brace_depth={brace_depth})")
        i += 1
        continue
    
    # Assignment or other statement
    if '=' in stripped or '++' in stripped:
        action = escape_mermaid(stripped)
        action_id = f"action{i}"
        print(f"  -> ACTION: {action}, current_nodes before={current_nodes}")
        current_nodes = [action_id]
        print(f"     current_nodes after={current_nodes}")
        i += 1
        continue
    
    # Skip standalone braces
    if stripped in ['{', '}']:
        i += 1
        continue
    
    i += 1

print("\nFinal if_stack:", if_stack)
print("Final current_nodes:", current_nodes)
