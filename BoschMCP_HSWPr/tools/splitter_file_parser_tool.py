"""
SplitterFileParser Tool

Searches splitter .xml files under a provided project root for failure word
definitions and extracts relevant metadata according to the SplitterfileHandling
specification (SHORT-NAME, DESCRIPTION, GOOD_CHECK_DESCRIPTION, ROOTCAUSE,
and debouncer/autosar config values).

If a failure word is not provided the tool returns an input_required response so
the client can prompt the user and re-call the tool with the value.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os
import xml.etree.ElementTree as ET
from .base_tool import BaseTool

logger = logging.getLogger(__name__)


class SplitterFileParserTool(BaseTool):
    def get_name(self) -> str:
        return "splitter_file_parser"

    def get_description(self) -> str:
        return (
            "Search splitter .xml files for a failure word and extract metadata "
            "(SHORT-NAME, DESCRIPTION, GOOD_CHECK_DESCRIPTION, ROOTCAUSE, debouncer config)."
        )

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "failure_word": {"type": "string", "description": "Failure word to search for"},
                "component_path": {"type": "string", "description": "Component path to search for splitter .xml files"}
            },
            "required": []
        }

    def _find_xml_files(self, root: str) -> List[str]:
        matches: List[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if fn.lower().endswith('.xml'):
                    matches.append(os.path.join(dirpath, fn))
        return matches

    def _safe_find_text(self, elem: Optional[ET.Element], tag: str) -> Optional[str]:
        if elem is None:
            return None
        # Try exact tag first
        child = elem.find(tag)
        if child is not None and child.text is not None:
            return child.text.strip()
        # Fall back to searching by local-name (ignore namespaces) and case-insensitive
        for c in list(elem):
            # get local name without namespace
            tagname = c.tag
            if isinstance(tagname, str) and '}' in tagname:
                local = tagname.split('}', 1)[1]
            else:
                local = tagname
            if local.lower() == tag.lower():
                return c.text.strip() if c.text is not None else None
        return None

    def _parse_value(self, val: Optional[str]):
        """Try to coerce string values to int or bool when appropriate."""
        if val is None:
            return None
        s = val.strip()
        if s == '':
            return None
        # boolean
        if s.lower() in ('true', 'false'):
            return s.lower() == 'true'
        # integer
        try:
            if s.endswith('ms'):
                return int(s[:-2].strip())
            return int(s)
        except Exception:
            # leave as string
            return s

    def _extract_failure_entries(self, xml_path: str, failure_word: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Search for FAILURE_WORD nodes anywhere
            for fw in root.findall('.//FAILURE_WORD'):
                short = self._safe_find_text(fw, 'SHORT-NAME')
                desc = self._safe_find_text(fw, 'DESCRIPTION')
                good = self._safe_find_text(fw, 'GOOD_CHECK_DESCRIPTION')
                rootcause = self._safe_find_text(fw, 'ROOTCAUSE')
                # TASK_REF may contain the task cycle reference or a pointer to a task
                task_ref = self._safe_find_text(fw, 'TASK_REF') or self._safe_find_text(fw, 'TASK-REF')

                # Some splitter files nest AUTOSAR / DebouncerAlgorithm near failure word
                autosar = fw.find('.//AUTOSAR')
                debouncer = None
                debouncer_type = None
                debouncer_values: Dict[str, Any] = {}
                if autosar is not None:
                    debouncer = autosar.find('.//DebouncerAlgorithm')
                if debouncer is not None:
                    debouncer_type = self._safe_find_text(debouncer, 'DebouncerType')
                    # try to extract time-based and counter-based fields
                    tb = debouncer.find('.//DebouncerTimebased')
                    if tb is not None:
                        for tag in ['DebouncetimeFailedthreshold', 'DebouncetimePassedthreshold']:
                            val = self._safe_find_text(tb, tag)
                            if val is not None:
                                debouncer_values[tag] = val
                    cb = debouncer.find('.//DebouncerCounterbased')
                    if cb is not None:
                        for tag in ['DebouncecounterIncrementstepsize', 'DebouncecounterDecrementstepsize',
                                    'DebouncecounterFailedthreshold', 'DebouncecounterPassedthreshold',
                                    'DebouncecounterJumpup', 'DebouncecounterJumpdown',
                                    'DebouncecounterJumpupvalue', 'DebouncecounterJumpdownvalue']:
                            val = self._safe_find_text(cb, tag)
                            if val is not None:
                                debouncer_values[tag] = val

                # also attempt to parse values to numeric/bool types for convenience
                debouncer_values_parsed: Dict[str, Any] = {}
                for k, v in debouncer_values.items():
                    debouncer_values_parsed[k] = self._parse_value(v)

                # Check if this failure_word entry matches the requested failure_word
                # The name may be in SHORT-NAME or the tag text itself
                name_to_check = (short or '').strip()
                if not name_to_check:
                    # fallback: try text content of the FAILURE_WORD element
                    if fw.text and fw.text.strip():
                        name_to_check = fw.text.strip()

                if name_to_check and name_to_check == failure_word:
                    # Try to interpret task_ref as a task cycle in ms if possible
                    task_cycle_ms = None
                    if task_ref:
                        parsed = self._parse_value(task_ref)
                        if isinstance(parsed, int):
                            task_cycle_ms = parsed

                    results.append({
                        'file': xml_path,
                        'short_name': short,
                        'description': desc,
                        'good_check_description': good,
                        'rootcause': rootcause,
                        'task_ref': task_ref,
                        'task_cycle_ms': task_cycle_ms,
                        'debouncer_type': debouncer_type,
                        'debouncer_values': debouncer_values,
                        'debouncer_values_parsed': debouncer_values_parsed
                    })

        except ET.ParseError as e:
            logger.warning(f"Failed to parse XML {xml_path}: {e}")
        except Exception as e:
            logger.exception(f"Error extracting failure entries from {xml_path}: {e}")

        return results

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            failure_word = params.get('failure_word') if params else None
            if not failure_word or str(failure_word).strip() == '':
                return {
                    'status': 'input_required',
                    'request_type': 'failure_word',
                    'message': 'Please provide the failure word to search splitter files for',
                    'prompt': 'Enter failure word:'
                }

            failure_word = str(failure_word).strip()
            component_path = params.get('component_path') if params else None
            if not component_path or str(component_path).strip() == '':
                return {
                    'status': 'input_required',
                    'request_type': 'component_path',
                    'message': 'Please provide the component path to search for splitter files.',
                    'prompt': 'Enter the component path (folder containing relevant splitter .xml files):'
                }

            component_path = str(component_path)
            logger.info(f"SplitterFileParser: searching for '{failure_word}' under {component_path}")

            xml_files = self._find_xml_files(component_path)
            logger.info(f"SplitterFileParser: found {len(xml_files)} xml files to scan")

            matches: List[Dict[str, Any]] = []
            for xf in xml_files:
                entries = self._extract_failure_entries(xf, failure_word)
                if entries:
                    matches.extend(entries)

            timestamp = datetime.utcnow().isoformat() + 'Z'

            if not matches:
                return {
                    'found': False,
                    'failure_word': failure_word,
                    'matches': [],
                    'message': f"No splitter entries found for failure word '{failure_word}' under {component_path}",
                    'timestamp': timestamp
                }

            return {
                'found': True,
                'failure_word': failure_word,
                'matches': matches,
                'count': len(matches),
                'message': f"Found {len(matches)} splitter entries for '{failure_word}'",
                'timestamp': timestamp
            }

        except Exception as e:
            logger.exception(f"SplitterFileParser execution failed: {e}")
            raise
