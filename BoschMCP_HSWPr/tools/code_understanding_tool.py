"""
CodeUnderstanding Tool

Searches the workspace for occurrences of a provided function or process name,
collects nearby code snippets, and builds a structured LLM prompt that asks the
client LLM to analyze the code to identify monitoring logic and execution
conditions related to a given failure word.

This tool does static text search only (no execution). If a function name is
missing it returns `input_required` so the caller can prompt the user.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os
import io
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class CodeUnderstandingTool(BaseTool):
    def get_name(self) -> str:
        return "code_understanding"

    def get_description(self) -> str:
        return (
            "Search for a function/process name in the workspace, collect code snippets, "
            "and return a prompt to help an LLM identify monitoring logic and execution conditions."
        )

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "function_name": {"type": "string", "description": "Function or process name to search for"},
                "failure_word": {"type": "string", "description": "Failure word being investigated (optional)"},
                "component_path": {"type": "string", "description": "Component path to search"},
                "max_snippets": {"type": "integer", "description": "Max code snippets to return", "default": 10}
            },
            "required": ["function_name"]
        }

    def _iter_text_files(self, root: str):
        for dirpath, dirnames, filenames in os.walk(root):
            # skip virtual env dirs, .git and test folders named 'tst'
            dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__', 'node_modules', '.venv', 'tst')]
            for fn in filenames:
                # consider common code/text files
                if fn.lower().endswith(('.py', '.c', '.cpp', '.h', '.hpp', '.java', '.js', '.ts', '.xml', '.json', '.cfg', '.ini', '.txt')):
                    yield os.path.join(dirpath, fn)

    def _collect_snippets(self, path: str, term: str, max_context: int = 3) -> List[Dict[str, Any]]:
        snippets: List[Dict[str, Any]] = []
        try:
            with io.open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return snippets

        for idx, line in enumerate(lines):
            if term in line:
                start = max(0, idx - max_context)
                end = min(len(lines), idx + max_context + 1)
                snippet = ''.join(lines[start:end])
                snippets.append({
                    'file': path,
                    'line_no': idx + 1,
                    'match_line': line.strip(),
                    'context': snippet
                })
        return snippets

    def _build_prompt(self, function_name: str, failure_word: Optional[str], snippets: List[Dict[str, Any]]) -> str:
        header = [
            f"Analyze the code for function/process: '{function_name}'.",
            "Goal: identify the monitoring logic and execution conditions that reference or trigger the provided failure word.",
        ]
        if failure_word:
            header.append(f"Failure word under investigation: '{failure_word}'.")

        header.append("Please identify:")
        header.append("1) Where the monitoring logic is implemented (file, function).")
        header.append("2) Execution conditions that set or evaluate the failure word.")
        header.append("3) Any debounce/counter logic, task cycles, or thresholds used.")
        header.append("4) External references (splitter files, TASK_REF, config lookups) and file names.")
        header.append("5) A short summary of the control flow that leads to the failure word being set.")

        prompt_parts = ['\n'.join(header), '\n--- Code snippets (limited) ---\n']
        for s in snippets:
            prompt_parts.append(f"File: {s['file']} (line {s['line_no']})\n{s['context']}\n---\n")

        prompt_parts.append("If the snippet is incomplete, try to infer likely surrounding logic and note any assumptions.")
        prompt_parts.append("Return a JSON object with keys: monitoring_location, execution_conditions, debounce_info, external_refs, summary, assumptions.")

        return '\n'.join(prompt_parts)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        function_name = params.get('function_name') if params else None
        failure_word = params.get('failure_word') if params else None
        component_path = params.get('component_path') if params else None
        process_locator_result = params.get('process_locator_result') if params else None
        flow_chart_result = params.get('flow_chart_result') if params else None
        gen_root = params.get('gen_root') if params else None
        
        if not function_name or str(function_name).strip() == '':
            return {
                'status': 'input_required',
                'request_type': 'function_name',
                'message': 'Please provide the function or process name to analyze',
                'prompt': 'Enter function/process name:'
            }
        if not component_path:
            component_path = os.getcwd()
        component_path = str(component_path)
        if not gen_root:
            gen_root = os.path.join(component_path, 'Gen')
        os.makedirs(gen_root, exist_ok=True)

        # Step 1: Ask client LLM to run the process_locator tool with component_path
        if not process_locator_result:
            return {
                'status': 'tool_request',
                'step': 1,
                'next_tool': 'process_locator',
                'next_tool_params': {
                    'component_path': component_path,
                    'failure_word': failure_word,
                    'function_name': function_name
                },
                'message': 'Step 1: Client LLM should call process_locator tool to get the process hierarchy, file names, and paths.',
                'instruction': 'Call process_locator and return the result in the next request as process_locator_result parameter.'
            }

        # Step 2: Fetch the process name, file name, and path from process_locator_result
        monitoring_summary = process_locator_result.get('monitoring_summary', [])
        if not monitoring_summary:
            return {'status': 'error', 'message': 'No monitoring summary found in process_locator_result.'}
        
        # Extract monitoring function and file path
        monitoring_function = monitoring_summary[0].get('monitoring_function')
        parent_process = monitoring_summary[0].get('parent_process')
        occurrence = monitoring_summary[0].get('occurrence', {})
        monitoring_file = occurrence.get('file')
        
        if not monitoring_function or not monitoring_file:
            return {'status': 'error', 'message': 'Could not extract monitoring function or file from process_locator_result.'}

        # Step 3: Ask LLM to call flow_chart_creator tool
        if not flow_chart_result:
            return {
                'status': 'tool_request',
                'step': 3,
                'next_tool': 'flow_chart_creator',
                'next_tool_params': {
                    'function_name': monitoring_function,
                    'file_path': monitoring_file,
                    'gen_root': gen_root
                },
                'message': f'Step 3: Client LLM should call flow_chart_creator tool for function {monitoring_function}.',
                'instruction': 'Call flow_chart_creator and return the result in the next request as flow_chart_result parameter.',
                'context': {
                    'monitoring_function': monitoring_function,
                    'parent_process': parent_process,
                    'monitoring_file': monitoring_file
                }
            }

        # Step 4: Read through the code to understand the function logic
        code_content = None
        try:
            with io.open(monitoring_file, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to read monitoring file: {e}'}

        # Collect snippets for the monitoring function and failure word
        snippets = self._collect_snippets(monitoring_file, monitoring_function, max_context=5)
        if failure_word:
            failure_snippets = self._collect_snippets(monitoring_file, failure_word, max_context=5)
            snippets.extend(failure_snippets)

        # Build analysis prompt
        analysis_prompt = self._build_prompt(monitoring_function, failure_word, snippets)

        # Step 5: Output the details of understanding
        return {
            'status': 'complete',
            'function_name': function_name,
            'failure_word': failure_word,
            'monitoring_function': monitoring_function,
            'parent_process': parent_process,
            'monitoring_file': monitoring_file,
            'flow_chart_result': flow_chart_result,
            'code_snippets': snippets,
            'analysis_prompt': analysis_prompt,
            'gen_root': gen_root,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': 'Code understanding complete. Review the analysis_prompt and code_snippets for detailed understanding.'
        }
