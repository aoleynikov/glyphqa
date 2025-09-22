"""
Generic Function Classifier - Works for any application
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re

@dataclass
class FunctionClassification:
    """Result of function classification."""
    domain: str
    confidence: float
    reasoning: str
    suggested_module: str

class GenericFunctionClassifier:
    """
    Generic classifier that works for any application.
    Uses semantic analysis to classify functions into logical modules.
    """
    
    def __init__(self, llm_provider=None, template_manager=None):
        self.llm_provider = llm_provider
        self.template_manager = template_manager
    
    def classify_function(self, function_name: str, function_content: str, 
                         function_type: str = None, 
                         application_context: str = None) -> FunctionClassification:
        """
        Classify a function into the appropriate domain using LLM analysis.
        
        Args:
            function_name: Name of the function
            function_content: JavaScript content of the function
            function_type: Explicit function type if known
            application_context: Context about the target application
            
        Returns:
            FunctionClassification: Classification result
        """
        
        if self.llm_provider and self.template_manager:
            return self._classify_with_llm(
                function_name, function_content, function_type, application_context
            )
        else:
            return self._classify_with_patterns(
                function_name, function_content, function_type
            )
    
    def _classify_with_llm(self, function_name: str, function_content: str,
                          function_type: str = None, 
                          application_context: str = None) -> FunctionClassification:
        """Use LLM to classify function semantically."""
        
        # Create classification prompt
        prompt = self.template_manager.render_template(
            'agent/function_classifier.j2',
            function_name=function_name,
            function_content=function_content,
            function_type=function_type,
            application_context=application_context
        )
        
        response = self.llm_provider.generate(prompt, function_content)
        
        # Parse LLM response
        return self._parse_classification_response(response)
    
    def _classify_with_patterns(self, function_name: str, function_content: str,
                               function_type: str = None) -> FunctionClassification:
        """Fallback pattern-based classification."""
        
        # Generic pattern matching
        patterns = {
            'auth': ['login', 'logout', 'auth', 'session', 'credential', 'signin', 'signout'],
            'navigation': ['navigate', 'goto', 'click', 'menu', 'nav', 'route', 'link'],
            'forms': ['fill', 'submit', 'form', 'input', 'select', 'checkbox', 'radio'],
            'validation': ['verify', 'check', 'assert', 'wait', 'expect', 'validate'],
            'data_management': ['create', 'add', 'edit', 'update', 'delete', 'remove', 'save'],
            'ui_interaction': ['click', 'hover', 'scroll', 'drag', 'drop', 'select'],
            'utilities': ['wait', 'timeout', 'utility', 'helper', 'common', 'base']
        }
        
        function_lower = function_name.lower()
        content_lower = function_content.lower()
        
        # Check patterns
        for domain, domain_patterns in patterns.items():
            for pattern in domain_patterns:
                if pattern in function_lower or pattern in content_lower:
                    return FunctionClassification(
                        domain=domain,
                        confidence=0.8,
                        reasoning=f"Pattern '{pattern}' found in function",
                        suggested_module=domain
                    )
        
        # Default to utilities
        return FunctionClassification(
            domain='utilities',
            confidence=0.5,
            reasoning='No specific patterns found',
            suggested_module='utilities'
        )
    
    def _parse_classification_response(self, response: str) -> FunctionClassification:
        """Parse LLM classification response."""
        # This would parse the LLM response and extract domain, confidence, etc.
        # For now, return a default classification
        return FunctionClassification(
            domain='utilities',
            confidence=0.7,
            reasoning='LLM classification',
            suggested_module='utilities'
        )
    
    def get_available_domains(self) -> List[str]:
        """Get list of available domain names."""
        return [
            'auth', 'navigation', 'forms', 'validation', 
            'data_management', 'ui_interaction', 'utilities'
        ]
    
    def create_module_structure(self, functions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Organize functions into modules based on classification.
        
        Args:
            functions: List of function dictionaries
            
        Returns:
            Dict mapping module names to lists of functions
        """
        modules = {}
        
        for func in functions:
            classification = self.classify_function(
                func.get('name', ''),
                func.get('content', ''),
                func.get('type', '')
            )
            
            module_name = classification.suggested_module
            if module_name not in modules:
                modules[module_name] = []
            
            modules[module_name].append(func)
        
        return modules
