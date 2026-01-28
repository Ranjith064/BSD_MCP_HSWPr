"""
Process Locator Tool

Given a failure word and a project root, this tool attempts to locate the process
that executes the monitoring logic that sets the failure word.

Algorithm (heuristic):
1) Find all process definition files (.proc) and extract process names.
2) Search all files under the root for occurrences of the failure word.
3) For each matching file/line, find the containing function (heuristic by scanning
   backwards for a function definition pattern).
4) If the function name matches a process name (or appears in .proc), we found it.
5) Otherwise, search the workspace for callers of the function; for each caller,
   find its containing function (parent) and repeat (walk up the call graph) until
   we find a process or reach a depth limit.
6) Write a Markdown report under <project_root>/Gen/<failure_word>/process_trace.md

Notes: this uses static heuristics and works best for C-like code and generated
task tables. It will try to be conservative and record evidence (file/line/context).
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os
import io
import re
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


def _iter_files(root: str, exts=('.proc', '.c', '.h', '.cpp', '.hpp', '.xml', '.py', '.txt')):
    for dirpath, dirnames, filenames in os.walk(root):
        # exclude common large or non-source folders, and test folders named 'tst'
        dirnames[:] = [d for d in dirnames if d not in ('.git', '__pycache__', 'node_modules', '.venv', 'tst')]
        for fn in filenames:
            if fn.lower().endswith(exts):
                yield os.path.join(dirpath, fn)


def _read_lines(path: str) -> List[str]:
    try:
        with io.open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except Exception:
        return []


def _find_proc_names(root: str) -> List[str]:
    procs: List[str] = []
    for p in _iter_files(root, exts=('.proc', '.xml')):
        lines = _read_lines(p)
        for ln in lines:
            # look for <PROCESS>name</PROCESS> or simple lines in .proc that name the process
            m = re.search(r'<PROCESS>([^<]+)</PROCESS>', ln)
            if m:
                procs.append(m.group(1).strip())
            else:
                # fallback: lines containing 'PROCESS' or typical .proc entries
                if '.proc' in p.lower() or 'process' in ln.lower():
                    # try extract token-like names
                    tokens = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]+)\b', ln)
                    for t in tokens:
                        # heuristic: uppercase + underscores often used
                        if any(c.isupper() for c in t) or '_' in t:
                            procs.append(t)
    # unique
    return list(dict.fromkeys(procs))


def _find_failure_occurrences(root: str, failure_word: str) -> List[Dict[str, Any]]:
    occ: List[Dict[str, Any]] = []
    # Only search C source files for failure word occurrences
    for p in _iter_files(root, exts=('.c',)):
        lines = _read_lines(p)
        for idx, ln in enumerate(lines):
            if failure_word in ln:
                start = max(0, idx - 3)
                end = min(len(lines), idx + 4)
                context = ''.join(lines[start:end])
                occ.append({'file': p, 'line_no': idx + 1, 'match_line': ln.strip(), 'context': context})
    return occ


def _find_containing_function(lines: List[str], idx: int) -> Optional[Dict[str, Any]]:
    # scan backwards from idx to find a line that looks like a function definition
    # pattern: something like 'type name(params) {' or 'name(params) {'
    for i in range(idx, -1, -1):
        line = lines[i].strip()
        # skip empty and comment lines
        if not line or line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            continue
        # combine current and next lines to handle defs split across lines
        window = '\n'.join(lines[max(0, i - 2):i + 1])
        # search for function name pattern
        m = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{]*\)\s*\{', window)
        if m:
            func = m.group(1)
            # find function start index within file for evidence
            # approximate start line as i-2
            start_line = max(1, i - 1)
            end_line = min(len(lines), i + 50)
            excerpt = ''.join(lines[start_line - 1:end_line])
            return {'function': func, 'start_line': start_line, 'end_line': end_line, 'excerpt': excerpt}
    return None


def _find_callers(root: str, function_name: str) -> List[Dict[str, Any]]:
    callers: List[Dict[str, Any]] = []
    pattern = re.compile(r'\b' + re.escape(function_name) + r'\s*\(')
    # Only search callers in C and header files
    for p in _iter_files(root, exts=('.c',)):
        lines = _read_lines(p)
        for idx, ln in enumerate(lines):
            if pattern.search(ln):
                start = max(0, idx - 3)
                end = min(len(lines), idx + 4)
                context = ''.join(lines[start:end])
                callers.append({'file': p, 'line_no': idx + 1, 'match_line': ln.strip(), 'context': context})
    return callers


class ProcessLocatorTool(BaseTool):
    def get_name(self) -> str:
        return 'process_locator'

    def get_description(self) -> str:
        return 'Locate the process executing monitoring for a given failure word and document the parent-child call chain.'

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'failure_word': {'type': 'string'},
                'project_root': {'type': 'string'},
                'component_path': {'type': 'string'}
            },
            'required': ['failure_word']
        }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        failure_word = params.get('failure_word') if params else None
        project_root = params.get('project_root') if params else None
        component_path = params.get('component_path') if params else None
        if not failure_word or str(failure_word).strip() == '':
            return {'status': 'input_required', 'request_type': 'failure_word', 'message': 'Please provide failure_word', 'prompt': 'Enter failure word:'}
        if not component_path or str(component_path).strip() == '':
            return {'status': 'input_required', 'request_type': 'component_path', 'message': 'Please provide component_path', 'prompt': 'Enter component path:'}
        failure_word = str(failure_word).strip()
        component_path = str(component_path).strip()
        # Normalize failure word for prompts/reports: remove leading 'FW_' if present
        normalized_fw = failure_word
        if normalized_fw.upper().startswith('FW_'):
            normalized_fw = normalized_fw[3:]

        logger.info(f"ProcessLocator: locating process for '{failure_word}' (normalized: '{normalized_fw}') under {component_path}")

        proc_names = _find_proc_names(component_path)
        logger.info(f"Found {len(proc_names)} process candidates from .proc/.xml files")

        # Search occurrences for both original and normalized failure word forms
        search_terms = list(dict.fromkeys([failure_word, normalized_fw]))
        # collect occurrences for any of the search terms (only .c/.h files)
        occurrences: List[Dict[str, Any]] = []
        for term in search_terms:
            occurrences.extend(_find_failure_occurrences(component_path, term))

        # de-duplicate occurrences by file+line
        seen = set()
        uniq_occ: List[Dict[str, Any]] = []
        for o in occurrences:
            key = (o['file'], o['line_no'])
            if key not in seen:
                seen.add(key)
                uniq_occ.append(o)

        occurrences = uniq_occ

        traces: List[Dict[str, Any]] = []

        for occ in occurrences:
            p = occ['file']
            lines = _read_lines(p)
            func_info = _find_containing_function(lines, occ['line_no'] - 1)
            if func_info:
                func_name = func_info['function']
                trace = [{'function': func_name, 'file': p, 'line': func_info['start_line'], 'evidence': occ['match_line']}]

                # walk up callers until we find process name or reach depth
                current = func_name
                depth = 0
                found_process = None
                while depth < 10 and current:
                    # check if current matches a process name
                    if current in proc_names:
                        found_process = current
                        break

                    # check callers
                    callers = _find_callers(component_path, current)
                    if not callers:
                        break
                    # take first caller as heuristic
                    caller = callers[0]
                    caller_lines = _read_lines(caller['file'])
                    parent_info = _find_containing_function(caller_lines, caller['line_no'] - 1)
                    if parent_info:
                        parent_name = parent_info['function']
                        trace.append({'function': parent_name, 'file': caller['file'], 'line': parent_info['start_line'], 'evidence': caller['match_line']})
                        current = parent_name
                    else:
                        break
                    depth += 1

                traces.append({'occurrence': occ, 'trace': trace, 'process': found_process})
            else:
                traces.append({'occurrence': occ, 'trace': [], 'process': None})

        # Derive summary: monitoring functions and their parent processes (if identified)
        monitoring_summary: List[Dict[str, Any]] = []
        for t in traces:
            if t.get('trace'):
                monitoring_fn = t['trace'][0]['function']
                # prefer identified process from .proc/.xml; otherwise use top-most caller as parent
                parent_proc = t.get('process') or (t['trace'][-1]['function'] if t['trace'] else None)
                # Collect direct callers of the monitoring function (step 3)
                direct_callers_raw = _find_callers(component_path, monitoring_fn)
                direct_callers: List[Dict[str, Any]] = []
                confirmed_parent = None
                for c in direct_callers_raw:
                    caller_lines = _read_lines(c['file'])
                    parent_info = _find_containing_function(caller_lines, c['line_no'] - 1)
                    parent_name = parent_info['function'] if parent_info else None
                    direct_callers.append({'file': c['file'], 'line': c['line_no'], 'match_line': c['match_line'], 'parent_function': parent_name})
                    # Heuristic to confirm parent process: prefer functions starting with PRC_ or names found in .proc/.xml
                    if not confirmed_parent:
                        if parent_name and (parent_name.startswith('PRC_') or parent_name in proc_names):
                            confirmed_parent = parent_name

                # If we didn't find a confirmed_parent from callers, keep existing parent_proc
                if not confirmed_parent:
                    confirmed_parent = parent_proc

                monitoring_summary.append({
                    'monitoring_function': monitoring_fn,
                    'parent_process': confirmed_parent,
                    'parent_process_source': 'proc_file' if confirmed_parent in proc_names else ('caller_search' if confirmed_parent and confirmed_parent != parent_proc else 'none'),
                    'direct_callers': direct_callers,
                    'occurrence': t['occurrence']
                })
            else:
                monitoring_summary.append({'monitoring_function': None, 'parent_process': None, 'direct_callers': [], 'occurrence': t['occurrence']})

        # write report under Gen/<normalized_failure_word>/process_trace.md
        gen_dir = os.path.join(component_path, 'Gen', normalized_fw)
        try:
            os.makedirs(gen_dir, exist_ok=True)
            report_path = os.path.join(gen_dir, 'process_trace.md')
            with io.open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# Process Trace for {normalized_fw}  (original: {failure_word})\n\n")
                f.write(f"Generated: {datetime.utcnow().isoformat()}Z\n\n")
                # Summary table
                f.write("## Summary\n\n")
                if monitoring_summary:
                    for s in monitoring_summary:
                        occ = s['occurrence']
                        f.write(f"- Occurrence: {os.path.relpath(occ['file'], component_path)}:{occ['line_no']} -> Monitoring function: {s['monitoring_function']} | Parent process/task: {s['parent_process']} (source: {s.get('parent_process_source')})\n")
                        # list direct callers (step 3)
                        if s.get('direct_callers'):
                            f.write(f"  Direct callers:\n")
                            for dc in s['direct_callers']:
                                f.write(f"    - {os.path.relpath(dc['file'], component_path)}:{dc['line']} -> parent function: {dc.get('parent_function')}\n")
                else:
                    f.write("No occurrences found.\n")

                f.write('\n---\n\n')

                for t in traces:
                    occ = t['occurrence']
                    f.write(f"## Occurrence: {occ['file']}:{occ['line_no']}\n")
                    f.write(f"Match line: {occ['match_line']}\n\n")
                    if t['trace']:
                        f.write("Call chain (child -> parent ...):\n")
                        for step in t['trace']:
                            f.write(f"- {step['function']}  (file: {step['file']} line: {step['line']})\n")
                    else:
                        f.write("No containing function found for this occurrence.\n")
                    if t['process']:
                        f.write(f"\nIdentified process: {t['process']}\n")
                    f.write('\n---\n\n')
        except Exception as e:
            logger.exception(f"Failed to write Gen report: {e}")
            return {'status': 'error', 'message': f'Failed to write report: {e}'}

        return {
            'status': 'ok',
            'failure_word': failure_word,
            'traces_count': len(traces),
            'report': report_path,
            'monitoring_summary': monitoring_summary
        }
