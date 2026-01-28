"""
FlowChartCreator Tool

Generates a detailed flow chart for a given function by analyzing its code and creates a Markdown (.md) file with the flow chart under the Gen folder.
"""
import re
from typing import Dict, Any
import os
import io
from .base_tool import BaseTool
from .flowchart_rules import flowchart_rules


class FlowChartCreatorTool(BaseTool):
    def get_name(self) -> str:
        return "flow_chart_creator"

    def get_description(self) -> str:
        return "Generate a detailed flow chart for a function and save it as a Markdown file in the Gen folder."

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "function_name": {"type": "string", "description": "Function name to generate flow chart for"},
                "file_path": {"type": "string", "description": "Path to the code file containing the function"},
                "gen_root": {"type": "string", "description": "Root Gen folder path to store the .md file"}
            },
            "required": ["function_name", "file_path", "gen_root"]
        }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        function_name = params.get("function_name")
        file_path = params.get("file_path")
        gen_root = params.get("gen_root")
        if not function_name or not file_path or not gen_root:
            return {"status": "input_required", "message": "function_name, file_path, and gen_root are required"}
        # Read the code and extract the function using regex (fallback approach)
        try:
            with io.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {e}"}

        # Use regex to find function definition
        try:
            func_pattern = rf'\b{re.escape(function_name)}\s*\([^)]*\)\s*\{{'
            match = re.search(func_pattern, code)
            if not match:
                return {"status": "error", "message": f"Function '{function_name}' not found in file. Pattern used: {func_pattern}"}
        except Exception as e:
            return {"status": "error", "message": f"Regex error while searching for function: {e}"}

        # Extract function body using bracket matching
        try:
            start_pos = match.start()
            brace_count = 0
            func_start = -1
            func_end = -1
            for i in range(start_pos, len(code)):
                if code[i] == '{':
                    if func_start == -1:
                        func_start = i
                    brace_count += 1
                elif code[i] == '}':
                    brace_count -= 1
                    if brace_count == 0 and func_start != -1:
                        func_end = i + 1
                        break
            if func_start == -1 or func_end == -1:
                return {"status": "error", "message": f"Could not extract complete function body. func_start={func_start}, func_end={func_end}, brace_count={brace_count}"}

        except Exception as e:
            return {"status": "error", "message": f"Error during function body extraction: {e}"}

        # Get function definition from start of line to end of function
        try:
            func_code = code[start_pos:func_end]
            func_lines = func_code.splitlines()
        except Exception as e:
            return {"status": "error", "message": f"Error splitting function code into lines: {e}"}

        # Helper function to escape special characters for Mermaid
        def escape_mermaid(text):
            # Escape special characters for Mermaid syntax (labels)
            text = text.replace('\t', ' ')
            text = text.replace('\n', ' ')
            text = text.replace('\r', ' ')
            text = text.strip()
            
            # Replace quotes and special chars that break Mermaid
            text = text.replace('"', "'")
            text = text.replace('#', 'num')
            text = text.replace('|', ' or ')
            text = text.replace('&', ' and ')
            
            # Remove extra spaces
            text = re.sub(r'\s+', ' ', text)
            
            # Don't truncate - let the rules handle length
            return text

        def sanitize_id(text):
            # Remove tabs, newlines, parentheses, semicolons, and replace all non-alphanumeric chars with _
            text = text.replace('\t', '').replace('\n', '').replace('\r', '')
            text = text.replace('(', '').replace(')', '').replace(';', '')
            text = re.sub(r'[^a-zA-Z0-9_]', '_', text)
            # Remove leading/trailing underscores and collapse multiple underscores
            text = re.sub(r'_+', '_', text).strip('_')
            # IDs must not start with a digit
            if text and text[0].isdigit():
                text = 'n_' + text
            return text

        # Generate flow chart using simplified approach
        flow_chart_md = f"# Flow Chart for {function_name}\n\n"
        flow_chart_md += "```mermaid\ngraph TD\n"
        flow_chart_md += "    start([Start])\n\n"
        
        nodes = []
        edges = []
        node_count = 0
        
        # Helpers to add nodes/edges and recursively parse blocks with nested if/else
        current_node = "start"

        def add_action_node(statement: str) -> str:
            nonlocal node_count, nodes
            node_count += 1
            action_id = f"action{node_count}"
            escaped_statement = escape_mermaid(statement)
            nodes.append(f"    {action_id}[\"{escaped_statement}\"]")
            return action_id

        def add_edge(frm: str, to: str, label: str | None = None):
            if label:
                edges.append(f"    {frm} -- {label} --> {to}")
            else:
                edges.append(f"    {frm} --> {to}")

        def add_if_node(condition_text: str) -> str:
            nonlocal node_count, nodes
            node_count += 1
            if_id = f"if{node_count}"
            nodes.append(f"    {if_id}{{{condition_text}?}}")
            return if_id

        def parse_block_for_branch(idx: int, parent_if_id: str, entry_label: str) -> tuple[str | None, int]:
            """
            Parse statements inside a { } block starting at line idx where func_lines[idx] starts with '{'.
            Returns (end_node_id or None if no actions, next_index_after_block)
            The first edge from parent_if_id to the first node will have the entry_label (Yes/No),
            subsequent edges are unlabeled.
            """
            i_local = idx
            if i_local >= len(func_lines) or not func_lines[i_local].strip().startswith('{'):
                return None, i_local
            brace_depth = 1
            i_local += 1
            branch_end: str | None = None
            first_connection_done = False
            while i_local < len(func_lines) and brace_depth > 0:
                inner_line = func_lines[i_local].strip()
                if not inner_line:
                    i_local += 1
                    continue
                if inner_line == '{':
                    brace_depth += 1
                    i_local += 1
                    continue
                if inner_line == '}':
                    brace_depth -= 1
                    i_local += 1
                    continue
                # Nested if
                if re.match(r'if\s*\(', inner_line):
                    # Extract condition
                    condition_match = re.search(r'if\s*\((.*?)\)', inner_line)
                    condition = escape_mermaid(flowchart_rules.remove_comments(condition_match.group(1).strip())) if condition_match else "condition"
                    nested_if_id = add_if_node(condition)
                    # Connect from parent_if_id or last node
                    if not first_connection_done:
                        add_edge(parent_if_id, nested_if_id, entry_label)
                        first_connection_done = True
                    else:
                        add_edge(branch_end, nested_if_id)
                    # Advance to YES block
                    i_local += 1
                    # Skip empties
                    while i_local < len(func_lines) and not func_lines[i_local].strip():
                        i_local += 1
                    # Parse YES
                    yes_end, i_local = parse_block_for_branch(i_local, nested_if_id, 'Yes')
                    # Skip empties
                    while i_local < len(func_lines) and not func_lines[i_local].strip():
                        i_local += 1
                    # Parse optional else
                    no_end = None
                    if i_local < len(func_lines) and re.match(r'else\s*(\{|$)', func_lines[i_local].strip()):
                        i_local += 1
                        while i_local < len(func_lines) and not func_lines[i_local].strip():
                            i_local += 1
                        no_end, i_local = parse_block_for_branch(i_local, nested_if_id, 'No')
                    # Merge for nested if
                    nonlocal node_count
                    node_count += 1
                    merge_id = f"merge{node_count}"
                    nodes.append(f"    {merge_id}[\" \"]")
                    if yes_end:
                        add_edge(yes_end, merge_id)
                    else:
                        add_edge(nested_if_id, merge_id, 'Yes')
                    if no_end:
                        add_edge(no_end, merge_id)
                    else:
                        add_edge(nested_if_id, merge_id, 'No')
                    branch_end = merge_id
                    continue
                # Regular statement inside branch
                processed_statement = flowchart_rules.process_statement(inner_line)
                if processed_statement:
                    action_id = add_action_node(processed_statement)
                    if not first_connection_done:
                        add_edge(parent_if_id, action_id, entry_label)
                        first_connection_done = True
                    else:
                        add_edge(branch_end, action_id)
                    branch_end = action_id
                i_local += 1
            return branch_end, i_local

        def parse_if_at(idx: int, connect_from: str) -> tuple[str, int]:
            """Parse an if-else starting at line idx; returns (merge_node_id, next_index)."""
            # Extract condition
            line = func_lines[idx].strip()
            condition_match = re.search(r'if\s*\((.*?)\)', line)
            condition = escape_mermaid(flowchart_rules.remove_comments(condition_match.group(1).strip())) if condition_match else "condition"
            if_id = add_if_node(condition)
            add_edge(connect_from, if_id)
            # Move to YES block
            idx += 1
            while idx < len(func_lines) and not func_lines[idx].strip():
                idx += 1
            yes_end, idx = parse_block_for_branch(idx, if_id, 'Yes')
            # Move to optional else
            while idx < len(func_lines) and not func_lines[idx].strip():
                idx += 1
            no_end = None
            if idx < len(func_lines) and re.match(r'else\s*(\{|$)', func_lines[idx].strip()):
                idx += 1
                while idx < len(func_lines) and not func_lines[idx].strip():
                    idx += 1
                no_end, idx = parse_block_for_branch(idx, if_id, 'No')
            # Create merge
            nonlocal node_count
            node_count += 1
            merge_id = f"merge{node_count}"
            nodes.append(f"    {merge_id}[\" \"]")
            if yes_end:
                add_edge(yes_end, merge_id)
            else:
                add_edge(if_id, merge_id, 'Yes')
            if no_end:
                add_edge(no_end, merge_id)
            else:
                add_edge(if_id, merge_id, 'No')
            return merge_id, idx
        
        # Skip the function signature
        found_func_start = False
        i = 0
        while i < len(func_lines):
            line = func_lines[i]
            stripped = line.strip()
            
            if not found_func_start:
                if '{' in stripped:
                    found_func_start = True
                i += 1
                continue
            
            # Skip empty lines
            if not stripped:
                i += 1
                continue
            
            # Skip standalone braces
            if stripped in ['{', '}']:
                i += 1
                continue
                
            # If statement (with recursive block parsing for nested conditionals)
            if re.match(r'if\s*\(', stripped):
                current_node, i = parse_if_at(i, current_node)
                continue
                
            # Regular statement
            else:
                # Apply flow chart rules
                processed_statement = flowchart_rules.process_statement(stripped)
                
                if processed_statement:
                    node_count += 1
                    action_id = f"action{node_count}"
                    escaped_statement = escape_mermaid(processed_statement)
                    nodes.append(f"    {action_id}[\"{escaped_statement}\"]")
                    
                    # Connect linear statements
                    edges.append(f"    {current_node} --> {action_id}")
                    
                    current_node = action_id
                    
            i += 1
        
        # No global merge needed; current_node already reflects last node
        
        # Write all components
        for node in nodes:
            flow_chart_md += f"{node}\n"
        
        flow_chart_md += f"\n    end_node([End])\n\n"
        
        for edge in edges:
            flow_chart_md += f"{edge}\n"
        
        flow_chart_md += f"    {current_node} --> end_node\n"
        flow_chart_md += "```\n"
        
        # Save to Gen folder
        os.makedirs(gen_root, exist_ok=True)
        md_path = os.path.join(gen_root, f"{function_name}.md")
        with io.open(md_path, 'w', encoding='utf-8') as f:
            f.write(flow_chart_md)

            # --- Additional: Generate Mermaid flowchart for function switches (#ifdef/#endif blocks) ---
            switch_blocks = []
            current_switch = None
            current_statements = []
            for line in func_lines:
                stripped = line.strip()
                match = re.match(r'#ifdef\s+(\w+)', stripped)
                if match:
                    if current_switch and current_statements:
                        switch_blocks.append((current_switch, current_statements))
                    current_switch = match.group(1)
                    current_statements = []
                    continue
                if re.match(r'#endif', stripped):
                    if current_switch and current_statements:
                        switch_blocks.append((current_switch, current_statements))
                    current_switch = None
                    current_statements = []
                    continue
                if current_switch and stripped and not stripped.startswith('#'):
                    processed = flowchart_rules.process_statement(stripped)
                    if processed:
                        current_statements.append(processed)
            if current_switch and current_statements:
                switch_blocks.append((current_switch, current_statements))

            if switch_blocks:
                switches_md = f"# Preprocessor Directive Function Switches for {function_name}\n\n"
                switches_md += "```mermaid\nflowchart TD\n"
                for switch_name, statements in switch_blocks:
                    subgraph_id = sanitize_id(switch_name)
                    switches_md += f"  subgraph {subgraph_id}[\"{switch_name}\"]\n"
                    switches_md += "    direction LR\n"
                    prev_id = None
                    for idx, stmt in enumerate(statements):
                        node_id = f"{subgraph_id}_{idx}"
                        switches_md += f"    {node_id}[{escape_mermaid(stmt)}]\n"
                        if prev_id:
                            switches_md += f"    {prev_id} --> {node_id}\n"
                        prev_id = node_id
                    switches_md += "  end\n"
                switches_md += "```\n"
                switches_path = os.path.join(gen_root, f"{function_name}_switches.md")
                with io.open(switches_path, 'w', encoding='utf-8') as f:
                    f.write(switches_md)

        return {"status": "ok", "message": f"Flow chart created at {md_path}", "md_path": md_path}
