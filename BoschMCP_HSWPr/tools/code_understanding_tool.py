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
                "project_root": {"type": "string", "description": "Root folder to search"},
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
        if not function_name or str(function_name).strip() == '':
            return {
                'status': 'input_required',
                'request_type': 'function_name',
                'message': 'Please provide the function or process name to analyze',
                'prompt': 'Enter function/process name:'
            }

        function_name = str(function_name).strip()
        failure_word = params.get('failure_word') if params else None
        project_root = params.get('project_root') if params else None
        max_snippets = params.get('max_snippets', 10) if params else 10

        if not project_root:
            project_root = os.getcwd()
        project_root = str(project_root)

        logger.info(f"CodeUnderstanding: searching for '{function_name}' under {project_root}")

        snippets_collected: List[Dict[str, Any]] = []
        for path in self._iter_text_files(project_root):
            snippets = self._collect_snippets(path, function_name)
            if snippets:
                snippets_collected.extend(snippets)
            if len(snippets_collected) >= max_snippets:
                break

        snippets_collected = snippets_collected[:max_snippets]
        prompt = self._build_prompt(function_name, failure_word, snippets_collected)

        return {
            'found': len(snippets_collected) > 0,
            'function_name': function_name,
            'failure_word': failure_word,
            'snippets': snippets_collected,
            'prompt': prompt,
            'count': len(snippets_collected),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
