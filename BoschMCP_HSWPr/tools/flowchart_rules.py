"""
Flow Chart Creation Rules and Guidelines

This module defines the rules for processing different types of code statements
when generating flow charts.
"""
import re
from typing import Dict, Any, Tuple, Optional


class FlowChartRules:
    """Rules engine for flow chart generation"""
    
    def __init__(self):
        self.rules = {
            'local_definition': self._process_local_definition,
            'rbmesg_receive': self._process_rbmesg_receive,
            'rbmesg_send': self._process_rbmesg_send,
            'rcvmesg': self._process_rcvmesg,  # New rule for RcvMESG
            'comment_removal': self._remove_comments,
            'general_statement': self._process_general_statement
        }
    
    def process_statement(self, statement: str) -> Optional[str]:
        """
        Process a code statement according to the defined rules
        
        Args:
            statement: Raw code statement
            
        Returns:
            Processed statement for flow chart or None if should be ignored
        """
        # Remove comments first
        clean_statement = self._remove_comments(statement)

        # Skip standalone comment banner lines (e.g., "/*...", "* ...", "...*/")
        banner_line = statement.strip()
        if (
            banner_line.startswith('/*') or
            banner_line.startswith('*') or
            banner_line.endswith('*/') or
            re.match(r"^/\*+\s*$", banner_line) or
            re.match(r"^\*+\s*$", banner_line) or
            re.match(r"^\*+/\s*$", banner_line)
        ):
            return None
        
        # Skip empty statements after comment removal
        if not clean_statement.strip():
            return None
            
        # Apply rules in order of priority
        
        # Rule for RcvMESG (without RBMESG prefix)
        rcvmesg_result = self._process_rcvmesg(clean_statement)
        if rcvmesg_result:
            return rcvmesg_result
        
        # Rule 3: RBMESG_RcvMESG processing (highest priority)
        rbmesg_rcv_result = self._process_rbmesg_receive(clean_statement)
        if rbmesg_rcv_result:
            return rbmesg_rcv_result
            
        # Rule 4: RBMESG_SendMESG processing  
        rbmesg_send_result = self._process_rbmesg_send(clean_statement)
        if rbmesg_send_result:
            return rbmesg_send_result
            
        # Rule 1: Local definitions
        local_def_result = self._process_local_definition(clean_statement)
        if local_def_result:
            return local_def_result
            
        # General statement processing
        return self._process_general_statement(clean_statement)
    
    def remove_comments(self, statement: str) -> str:
        """
        Rule 2: Remove comments from code statements (public method)
        
        Removes:
        - Single line comments (//)
        - Multi-line comments (/* */)
        - Inline comments
        """
        return self._remove_comments(statement)
    
    def _remove_comments(self, statement: str) -> str:
        """
        Rule 2: Remove comments from code statements
        
        Removes:
        - Single line comments (//)
        - Multi-line comments (/* */)
        - Inline comments
        """
        # Remove single line comments
        statement = re.sub(r'//.*$', '', statement)
        
        # Remove multi-line comments (simple case - same line)
        statement = re.sub(r'/\*.*?\*/', '', statement)
        
        return statement.strip()
    
    def _process_local_definition(self, statement: str) -> Optional[str]:
        """
        Rule 1: Process local variable definitions
        
        For definitions like "Boolean A; // comment"
        Return only "Boolean A" (type and name until semicolon)
        """
        # Pattern to match variable declarations: type name; or type name[size];
        pattern = r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\[[^\]]*\])?\s*;'
        match = re.match(pattern, statement.strip())
        
        if match:
            type_name = match.group(2)
            var_name = match.group(3)
            return f"{type_name} {var_name}"
            
        return None
    
    def _process_rcvmesg(self, statement: str) -> Optional[str]:
        """
        Rule for RcvMESG function calls (without RBMESG prefix)
        
        For "RcvMESG(A, B);" 
        Return "Receive the value from B and store it in A"
        """
        # Check for RcvMESG pattern (but not RBMESG_RcvMESG)
        if 'RBMESG_RcvMESG' in statement:
            return None  # Let the RBMESG rule handle this
            
        pattern = r'RcvMESG\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        match = re.search(pattern, statement)
        
        if match:
            var_a = match.group(1).strip().replace('&', '').strip()  # Remove address operator
            var_b = match.group(2).strip()
            return f"Receive the value from {var_b} and store it in {var_a}"
            
        return None
    
    def _process_rbmesg_receive(self, statement: str) -> Optional[str]:
        """
        Rule 3: Process RBMESG_RcvMESG function calls
        
        For "RBMESG_RcvMESG(A, B);" 
        Return "Receive the value from B and store it in A"
        """
        # Check for RBMESG_RcvMESG pattern (with or without &)
        pattern = r'RBMESG_RcvMESG\s*\(\s*(&?\s*[^,]+)\s*,\s*([^)]+)\s*\)'
        match = re.search(pattern, statement)
        
        if match:
            var_a = match.group(1).strip().replace('&', '').strip()  # Remove address operator
            var_b = match.group(2).strip()
            return f"Receive the value from {var_b} and store it in {var_a}"
            
        return None
    
    def _process_rbmesg_send(self, statement: str) -> Optional[str]:
        """
        Rule 4: Process RBMESG_SendMESG function calls
        
        For "RBMESG_SendMESG(A, B);"
        Return "Update the interface A with the value from B"
        """
        pattern = r'RBMESG_SendMESG\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        match = re.search(pattern, statement)
        
        if match:
            var_a = match.group(1).strip()
            var_b = match.group(2).strip()
            return f"Update the interface {var_a} with the value from {var_b}"
            
        return None
    
    def _process_general_statement(self, statement: str) -> str:
        """
        Process general statements (fallback)
        """
        # Remove semicolons and extra whitespace
        clean = statement.replace(';', '').strip()
        
        # Handle specific function calls that aren't RBMESG
        if 'RcvMESG' in clean and 'RBMESG_RcvMESG' not in clean:
            return "Receive message"
        if 'SendMESG' in clean and 'RBMESG_SendMESG' not in clean:
            return "Send message"
        if 'RBMICSYS_WritePort' in clean:
            return "Write to port"
        if 'WritePort' in clean:
            return "Write to port"
        
        # Handle if conditions - don't truncate them
        if clean.startswith('if'):
            return clean
            
        # For other statements, limit length for readability but keep more text
        if len(clean) > 60:
            clean = clean[:57] + "..."
            
        return clean if clean else None


# Global instance for easy access
flowchart_rules = FlowChartRules()