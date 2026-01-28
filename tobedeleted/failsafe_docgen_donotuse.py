from typing import Dict, Any
from .base_feature import BaseFeature


class FailsafeDocGenFeature(BaseFeature):
    name = "FailsafeDocGen"
    description = "Failsafe document generation workflow - returns execution plan for client LLM"

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = params or {}
        failure_word = params.get("failure_word") or params.get("fw_name")
        if not failure_word or not isinstance(failure_word, str) or failure_word.strip() == "":
            return {
                "status": "input_required",
                "request_type": "failure_word",
                "message": "Please provide the failure word to proceed with failsafe document generation",
                "prompt": "Enter failure word:"
            }


        # Always require project_root from user input, never infer or default
        project_root = params.get("project_root")
        if not project_root or not isinstance(project_root, str) or project_root.strip() == "":
            return {
                "status": "input_required",
                "request_type": "project_root",
                "message": "Please provide the project root folder path (absolute path to the root of your project)",
                "prompt": "Enter project root folder path:"
            }

        failure_word = failure_word.strip()
        project_root = project_root.strip()

        steps = [
            {"step": 1, "description": "Validate failure word name", "action": "manual", "details": f"Confirmed failure word: {failure_word}"},
            {"step": 2, "description": "Validate project root folder path", "action": "manual", "details": f"Confirmed project root: {project_root}"},
            {"step": 3, "description": "Find component containing the failure word", "action": "tool_call", "tool": "find_component", "params": {"failure_word": failure_word, "project_root": project_root}, "expected_output": "component_name", "output_variable": "component_name"},
            {"step": 4, "description": "Locate process and function where monitoring is implemented", "action": "tool_call", "tool": "process_locator", "params": {"failure_word": failure_word, "project_root": project_root}, "expected_output": "monitoring_summary, report_path", "output_variable": "process_info"},
            {"step": 5, "description": "Understand the monitoring code logic", "action": "tool_call", "tool": "code_understanding", "params": {"function_name": "{{process_info.monitoring_summary[0].monitoring_function}}", "failure_word": failure_word, "project_root": project_root, "max_snippets": 10}, "depends_on": ["step_4"], "expected_output": "code_snippets, analysis_prompt", "output_variable": "code_analysis"},
            {"step": 6, "description": "Extract failure word configuration from splitter file", "action": "tool_call", "tool": "splitter_file_parser", "params": {"failure_word": failure_word, "project_root": project_root}, "expected_output": "splitter_config (SHORT-NAME, DESCRIPTION, GOOD_CHECK_DESCRIPTION, ROOTCAUSE, AUTOSAR debouncer config, TASK_REF)", "output_variable": "splitter_config"},
            {"step": 7, "description": "Calculate filter time (detection and recovery)", "action": "calculation", "details": "If DebouncerType is 'CounterBased': use splitter_config data and formulas from SplitterfileHandling.md. If 'MonitoringInternal': search relevant .c files for counter logic and calculate manually.", "depends_on": ["step_6"], "calculation_reference": "SplitterfileHandling.md", "formulas": {"failure_filter_time": "IF (JumpUpState == TRUE) { StepsNeeded = (Fail_Threshold - JumpUpValue) / IncrementStep } ELSE { StepsNeeded = (Fail_Threshold - Pass_Threshold) / IncrementStep }; Failure_FilterTime = Task_Cycle × StepsNeeded", "recovery_filter_time": "IF (JumpDownState == TRUE) { StepsNeeded = (JumpDownValue - Pass_Threshold) / DecrementStep } ELSE { StepsNeeded = (Fail_Threshold - Pass_Threshold) / DecrementStep }; Recovery_FilterTime = Task_Cycle × StepsNeeded"}, "output_variable": "filter_times"},
            {"step": 8, "description": "Generate final output document", "action": "format_output", "details": "Create markdown document following Output_format.md template with table format. Include: Purpose, Detection Condition, Detection Time (from filter_times), Monitoring Period, Recovery Condition, Notes. Save as [Component]_FailSafe.md", "depends_on": ["step_3", "step_4", "step_5", "step_6", "step_7"], "output_format_reference": "Output_format.md", "output_file": "{{component_name}}_FailSafe.md", "output_location": "Output/"}
        ]

        prompt = (
            f"You are the orchestrator for the failsafe document generation workflow for failure word '{failure_word}'.\n\n"
            f"IMPORTANT: Whenever this workflow is triggered, you MUST re-execute ALL steps from the beginning, regardless of any previous runs or cached results. Do not reuse or assume any prior outputs.\n\n"
            f"CRITICAL: You MUST always prompt the user to enter the project root folder path (project_root). Do NOT use any default, cached, previously inferred, or pre-filled value for project_root. Only proceed after the user explicitly provides this input.\n\n"
            f"Execute the following 8-step plan now. Call the specified MCP tools, perform the calculations, and generate the final document.\n\n"
            f"1. Validation (done): failure_word='{failure_word}', project_root='{project_root}'.\n"
            f"2. Call 'find_component' with params: {{'failure_word': '{failure_word}', 'project_root': '{project_root}'}} -> save output as component_name.\n"
            f"3. Call 'process_locator' with params: {{'failure_word': '{failure_word}', 'project_root': '{project_root}'}} -> from result.monitoring_summary take monitoring_function and parent_process; also review result.report.\n"
            f"4. Call 'code_understanding' with params: {{'function_name': '<monitoring_function from step 3>', 'failure_word': '{failure_word}', 'project_root': '{project_root}', 'max_snippets': 10}} -> save snippets and analysis_prompt.\n"
            f"5. Call 'splitter_file_parser' with params: {{'failure_word': '{failure_word}', 'project_root': '{project_root}'}} -> capture SHORT-NAME, DESCRIPTION, GOOD_CHECK_DESCRIPTION, ROOTCAUSE, DebouncerType, TASK_REF, and debouncer parameters.\n"
            f"6. Compute detection and recovery filter times:\n"
            f"   - If DebouncerType='CounterBased': use formulas from SplitterfileHandling.md with extracted parameters.\n"
            f"   - If DebouncerType='MonitoringInternal': search the code for counter logic and compute manually.\n"
            f"   - Important: Use formulas; do not rely on XML comments.\n"
            f"7. Create the final markdown using Output_format.md. Filename: <component_name>_FailSafe.md. Include Purpose, Detection Condition, Detection Time, Monitoring Period, Recovery Condition, Notes. Save to Output/.\n\n"
            f"Return the final document and a concise summary of findings."
        )

        return {
            "status": "plan_ready",
            "failure_word": failure_word,
            "project_root": project_root,
            "execution_plan": {"steps": steps},
            "prompt": prompt,
            "tools_required": ["find_component", "process_locator", "code_understanding", "splitter_file_parser"],
            "reference_documents": ["SplitterfileHandling.md", "Output_format.md"],
            "expected_artifacts": [
                "process_trace.md (from process_locator)",
                "[Component]_FailSafe.md (final output)"
            ]
        }
