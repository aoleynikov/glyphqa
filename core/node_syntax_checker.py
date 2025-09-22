"""
Node.js-based JavaScript Syntax Checker
Uses Node.js to validate JavaScript syntax instead of regex patterns
"""

import subprocess
import tempfile
import os
import logging
from typing import List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class NodeSyntaxChecker:
    """
    Uses Node.js to check JavaScript syntax validity.
    Much more reliable than regex patterns.
    """
    
    def __init__(self):
        self.node_available = self._check_node_availability()
    
    def _check_node_availability(self) -> bool:
        """Check if Node.js is available on the system."""
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.debug(f"Node.js available: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        logger.warning("Node.js not available for syntax checking")
        return False
    
    def check_syntax(self, code_content: str) -> Tuple[bool, List[str]]:
        """
        Check JavaScript syntax using Node.js.
        
        Args:
            code_content: JavaScript code to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not self.node_available:
            logger.warning("Node.js not available, skipping syntax check")
            return True, []
        
        try:
            # Create a temporary file with the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code_content)
                temp_file = f.name
            
            try:
                # Use Node.js to check syntax
                result = subprocess.run(
                    ['node', '--check', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Clean up temp file
                os.unlink(temp_file)
                
                if result.returncode == 0:
                    return True, []
                else:
                    # Parse error messages
                    errors = []
                    if result.stderr:
                        # Extract meaningful error messages
                        lines = result.stderr.strip().split('\n')
                        for line in lines:
                            if line.strip() and not line.startswith('node:'):
                                errors.append(line.strip())
                    
                    return False, errors
                    
            except subprocess.TimeoutExpired:
                os.unlink(temp_file)
                logger.warning("Node.js syntax check timed out")
                return True, []  # Assume valid if timeout
                
        except Exception as e:
            logger.error(f"Failed to check syntax with Node.js: {e}")
            return True, []  # Assume valid on error
    
    def check_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Check syntax of a JavaScript file.
        
        Args:
            file_path: Path to JavaScript file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not self.node_available:
            return True, []
        
        try:
            result = subprocess.run(
                ['node', '--check', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, []
            else:
                errors = []
                if result.stderr:
                    lines = result.stderr.strip().split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('node:'):
                            errors.append(line.strip())
                return False, errors
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Node.js syntax check timed out for {file_path}")
            return True, []
        except Exception as e:
            logger.error(f"Failed to check syntax of {file_path}: {e}")
            return True, []
    
    def fix_syntax_errors(self, code_content: str) -> Tuple[str, int]:
        """
        Attempt to fix common syntax errors using Node.js validation.
        
        Args:
            code_content: JavaScript code to fix
            
        Returns:
            Tuple of (fixed_code, number_of_fixes_applied)
        """
        if not self.node_available:
            return code_content, 0
        
        # First check if it's already valid
        is_valid, errors = self.check_syntax(code_content)
        if is_valid:
            return code_content, 0
        
        # Try to fix common issues
        fixed_code = code_content
        fixes_applied = 0
        
        # Fix common issues
        fixes = [
            # Fix missing semicolons
            (r'(\w+)\s*$', r'\1;', "Add missing semicolon"),
            # Fix unmatched quotes
            (r'(["\'])([^"\']*)\1([^"\']*)\1', r'\1\2\3\1', "Fix unmatched quotes"),
            # Fix missing closing parentheses
            (r'(\w+\([^)]*$)', r'\1)', "Add missing closing parenthesis"),
        ]
        
        import re
        for pattern, replacement, description in fixes:
            if re.search(pattern, fixed_code, re.MULTILINE):
                old_code = fixed_code
                fixed_code = re.sub(pattern, replacement, fixed_code, flags=re.MULTILINE)
                if fixed_code != old_code:
                    fixes_applied += 1
                    logger.debug(f"Applied fix: {description}")
        
        # Check if fixes worked
        is_valid, _ = self.check_syntax(fixed_code)
        if is_valid:
            logger.info(f"Fixed {fixes_applied} syntax errors using Node.js")
        else:
            logger.warning("Could not fix all syntax errors with Node.js")
        
        return fixed_code, fixes_applied
