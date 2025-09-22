"""
SDK Build Integration - Connects SDK data with build processes
"""

import logging
from typing import Dict, List, Optional, Any
from .sdk_data_aggregator import SdkDataAggregator, SdkBuildContext
from .generic_modular_sdk_manager import GenericModularSdkManager

logger = logging.getLogger(__name__)

class SdkBuildIntegration:
    """
    Integrates SDK data with the build process.
    
    Responsibilities:
    - Provide SDK context to build agents
    - Handle function selection and optimization
    - Manage SDK imports and dependencies
    - Ensure build processes use correct SDK functions
    """
    
    def __init__(self, modular_sdk_manager: GenericModularSdkManager, 
                 template_manager, llm_provider=None):
        self.sdk_manager = modular_sdk_manager
        self.template_manager = template_manager
        self.llm_provider = llm_provider
        
        # Initialize data aggregator
        self.data_aggregator = SdkDataAggregator(modular_sdk_manager)
    
    def get_build_context_for_scenario(self, scenario_name: str, 
                                      scenario_steps: List[str] = None) -> SdkBuildContext:
        """
        Get optimized SDK context for a specific scenario build.
        
        Args:
            scenario_name: Name of the scenario being built
            scenario_steps: List of scenario steps to optimize function selection
            
        Returns:
            SdkBuildContext: Optimized SDK context
        """
        
        # Analyze scenario to determine needed functions
        target_functions = self._analyze_scenario_needs(scenario_name, scenario_steps)
        
        # Get build context
        context = self.data_aggregator.get_build_context(
            scenario_name=scenario_name,
            target_functions=target_functions
        )
        
        return context
    
    def _analyze_scenario_needs(self, scenario_name: str, 
                               scenario_steps: List[str] = None) -> List[str]:
        """
        Analyze scenario to determine which SDK functions are needed.
        
        Args:
            scenario_name: Name of the scenario
            scenario_steps: List of scenario steps
            
        Returns:
            List[str]: Names of needed functions
        """
        
        if not scenario_steps:
            # Return all available functions if no specific steps
            return None
        
        # Use LLM to analyze scenario needs
        if self.llm_provider and self.template_manager:
            return self._analyze_with_llm(scenario_name, scenario_steps)
        else:
            return self._analyze_with_patterns(scenario_name, scenario_steps)
    
    def _analyze_with_llm(self, scenario_name: str, scenario_steps: List[str]) -> List[str]:
        """Use LLM to analyze scenario needs."""
        
        # Create analysis prompt
        prompt = self.template_manager.render_template(
            'agent/scenario_function_analyzer.j2',
            scenario_name=scenario_name,
            scenario_steps=scenario_steps,
            available_functions=self.data_aggregator.get_sdk_summary_for_llm()
        )
        
        response = self.llm_provider.generate(prompt, "\n".join(scenario_steps))
        
        # Parse response to extract function names
        return self._parse_function_analysis_response(response)
    
    def _analyze_with_patterns(self, scenario_name: str, scenario_steps: List[str]) -> List[str]:
        """Fallback pattern-based analysis."""
        
        needed_functions = []
        
        # Simple pattern matching
        for step in scenario_steps:
            step_lower = step.lower()
            
            if any(word in step_lower for word in ['login', 'auth', 'signin']):
                needed_functions.extend(['loginAsAdmin', 'loginAsUser', 'fillLoginForm'])
            
            if any(word in step_lower for word in ['logout', 'signout']):
                needed_functions.extend(['logout', 'verifyLogout'])
            
            if any(word in step_lower for word in ['create', 'add', 'new']):
                needed_functions.extend(['createUser', 'createAdmin', 'fillForm'])
            
            if any(word in step_lower for word in ['delete', 'remove']):
                needed_functions.extend(['deleteUser', 'removeUser'])
            
            if any(word in step_lower for word in ['verify', 'check', 'assert']):
                needed_functions.extend(['verifyDashboard', 'verifyLogin', 'verifyUser'])
        
        return list(set(needed_functions))  # Remove duplicates
    
    def _parse_function_analysis_response(self, response: str) -> List[str]:
        """Parse LLM response to extract function names."""
        
        # This would parse the LLM response
        # For now, return empty list
        return []
    
    def provide_sdk_context_to_builder(self, scenario_name: str, 
                                     current_step: str,
                                     accumulated_steps: List[str] = None) -> str:
        """
        Provide SDK context to the builder agent.
        
        Args:
            scenario_name: Name of the scenario
            current_step: Current step being built
            accumulated_steps: Previously executed steps
            
        Returns:
            str: Formatted SDK context for the builder
        """
        
        # Get build context
        context = self.get_build_context_for_scenario(
            scenario_name, accumulated_steps
        )
        
        # Format context for builder
        formatted_context = self.template_manager.render_template(
            'agent/sdk_build_context.j2',
            sdk_context=context
        )
        
        return formatted_context
    
    def get_optimized_imports_for_spec(self, scenario_name: str, 
                                      spec_content: str) -> str:
        """
        Get optimized imports for a specific spec.
        
        Args:
            scenario_name: Name of the scenario
            spec_content: Content of the spec being built
            
        Returns:
            str: Optimized import statements
        """
        
        # Analyze spec content to determine needed functions
        needed_functions = self._analyze_spec_content(spec_content)
        
        # Get context with only needed functions
        context = self.data_aggregator.get_build_context(
            scenario_name=scenario_name,
            target_functions=needed_functions
        )
        
        return context.function_imports
    
    def _analyze_spec_content(self, spec_content: str) -> List[str]:
        """Analyze spec content to determine needed functions."""
        
        # Simple analysis - look for function calls
        import re
        
        # Find function calls in the spec
        function_calls = re.findall(r'await\s+(\w+)\s*\(', spec_content)
        
        return list(set(function_calls))  # Remove duplicates
    
    def validate_sdk_usage_in_spec(self, spec_content: str) -> Dict[str, Any]:
        """
        Validate that SDK functions are used correctly in a spec.
        
        Args:
            spec_content: Content of the spec to validate
            
        Returns:
            Dict with validation results
        """
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Check for common issues
        if 'import' not in spec_content:
            validation_results['warnings'].append("No import statements found")
        
        if 'await' not in spec_content:
            validation_results['warnings'].append("No async function calls found")
        
        # Check for undefined function calls
        import re
        function_calls = re.findall(r'await\s+(\w+)\s*\(', spec_content)
        
        for func_call in function_calls:
            if not self.data_aggregator.get_function_by_name(func_call):
                validation_results['errors'].append(f"Undefined function: {func_call}")
                validation_results['valid'] = False
        
        return validation_results
    
    def get_sdk_usage_statistics(self) -> Dict[str, Any]:
        """Get statistics about SDK usage."""
        
        stats = {
            'total_functions': 0,
            'modules': {},
            'most_used_functions': [],
            'unused_functions': []
        }
        
        # Count functions by module
        for module_name, functions in self.sdk_manager.modules.items():
            stats['modules'][module_name] = len(functions)
            stats['total_functions'] += len(functions)
        
        return stats
