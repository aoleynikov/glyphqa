"""
LLM-powered Syntax Error Fixer - Uses LLM to detect and fix JavaScript syntax errors
"""

import logging
from typing import List, Tuple, Optional
import json

logger = logging.getLogger(__name__)

class LLMSyntaxFixer:
    """
    LLM-powered syntax error finder and fixer.
    Uses LLM to intelligently detect and fix JavaScript syntax errors.
    """
    
    def __init__(self, llm_provider, template_manager):
        self.llm_provider = llm_provider
        self.template_manager = template_manager
    
    def find_syntax_errors(self, code_content: str) -> List[dict]:
        """
        Use Node.js to find syntax errors in JavaScript code.
        
        Args:
            code_content: JavaScript code to analyze
            
        Returns:
            List of error objects with details
        """
        try:
            from .node_syntax_checker import NodeSyntaxChecker
            checker = NodeSyntaxChecker()
            
            is_valid, errors = checker.check_syntax(code_content)
            
            if is_valid:
                return []
            
            # Convert Node.js errors to our format
            error_objects = []
            for i, error in enumerate(errors):
                error_objects.append({
                    "line": i + 1,
                    "column": 1,
                    "message": error,
                    "severity": "error",
                    "code": ""
                })
            
            return error_objects
                
        except Exception as e:
            logger.error(f"Failed to find syntax errors: {e}")
            return []
    
    def fix_syntax_errors(self, code_content: str, errors: List[dict]) -> Tuple[str, int]:
        """
        Use Node.js to fix syntax errors in JavaScript code.
        
        Args:
            code_content: JavaScript code to fix
            errors: List of syntax errors to fix
            
        Returns:
            Tuple of (fixed_code, number_of_fixes_applied)
        """
        if not errors:
            return code_content, 0
        
        try:
            from .node_syntax_checker import NodeSyntaxChecker
            checker = NodeSyntaxChecker()
            
            fixed_content, fixes_applied = checker.fix_syntax_errors(code_content)
            return fixed_content, fixes_applied
            
        except Exception as e:
            logger.error(f"Failed to fix syntax errors: {e}")
            return code_content, 0
    
    def fix_file(self, file_path: str) -> Tuple[bool, int]:
        """
        Fix syntax errors in a JavaScript file using Node.js.
        
        Args:
            file_path: Path to JavaScript file
            
        Returns:
            Tuple of (success, number_of_fixes_applied)
        """
        try:
            from .node_syntax_checker import NodeSyntaxChecker
            checker = NodeSyntaxChecker()
            
            # Check if file has syntax errors
            is_valid, errors = checker.check_file(file_path)
            
            if is_valid:
                logger.info(f"No syntax errors found in {file_path}")
                return True, 0
            
            logger.info(f"Found {len(errors)} syntax errors in {file_path}")
            for error in errors:
                logger.debug(f"Error: {error}")
            
            # Read file content and fix
            with open(file_path, 'r') as f:
                code_content = f.read()
            
            fixed_code, fixes_applied = checker.fix_syntax_errors(code_content)
            
            if fixes_applied > 0:
                # Write back to file
                with open(file_path, 'w') as f:
                    f.write(fixed_code)
                
                logger.info(f"🔧 Fixed {fixes_applied} syntax errors in {file_path}")
                return True, fixes_applied
            else:
                logger.warning(f"Node.js could not fix syntax errors in {file_path}")
                return False, 0
                
        except Exception as e:
            logger.error(f"Failed to fix syntax errors in {file_path}: {e}")
            return False, 0
    
    def fix_all_errors(self, code_content: str) -> Tuple[str, int]:
        """
        Iteratively fix all syntax errors in code using Node.js.
        
        Args:
            code_content: JavaScript code to fix
            
        Returns:
            Tuple of (fixed_code, number_of_fixes_applied)
        """
        try:
            from .node_syntax_checker import NodeSyntaxChecker
            checker = NodeSyntaxChecker()
            
            # Use Node.js to fix all errors at once
            fixed_code, fixes_applied = checker.fix_syntax_errors(code_content)
            return fixed_code, fixes_applied
            
        except Exception as e:
            logger.error(f"Failed to fix all syntax errors: {e}")
            return code_content, 0
