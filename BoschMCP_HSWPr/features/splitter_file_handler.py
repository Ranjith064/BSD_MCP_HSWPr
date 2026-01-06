from typing import Dict, Any
from .base_feature import BaseFeature
from ..tools.tool_registry import tool_registry


class SplitterFileHandlerFeature(BaseFeature):
    name = "SplitterFileHandler"
    description = "Wrapper feature that calls the splitter_file_parser tool"

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # allow aliases for parameters
        failure_word = params.get('failure_word') or params.get('fw_name') or params.get('failureWord')
        project_root = params.get('project_root') or params.get('root') or params.get('projectRoot')

        tool_params = {}
        if failure_word:
            tool_params['failure_word'] = failure_word
        if project_root:
            tool_params['project_root'] = project_root

        # Call the splitter_file_parser tool
        if not tool_registry.has_tool('splitter_file_parser'):
            raise RuntimeError('splitter_file_parser tool not available')

        result = tool_registry.execute_tool('splitter_file_parser', tool_params)
        return result
