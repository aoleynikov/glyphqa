"""
Step Mapper - Maps individual steps to JavaScript lines for composition.
"""
import logging
from typing import List, Dict, Any
from .steps import Step, Action, Check, Precondition

logger = logging.getLogger(__name__)


class StepMapper:
    """Maps individual steps to JavaScript lines for template composition."""
    
    def __init__(self, llm_provider, template_manager, target):
        self.llm_provider = llm_provider
        self.template_manager = template_manager
        self.target = target
    
    def _validate_generated_code(self, js_lines: List[str], context: Dict[str, Any]) -> List[str]:
        """Validate generated code using enhanced syntax validation."""
        from .node_syntax_checker import NodeSyntaxChecker
        
        validator = NodeSyntaxChecker()
        code_content = '\n'.join(js_lines)
        is_valid, errors = validator.check_syntax(code_content)
        
        if not is_valid:
            fixed_content, fixes_applied = validator.fix_syntax_errors(code_content)
            if fixes_applied > 0:
                fixed_lines = fixed_content.split('\n')
            else:
                fixed_lines = js_lines
        else:
            fixed_lines = js_lines
        
        if errors:
            logger.warning(f"Found {len(errors)} syntax errors in generated code")
            for error in errors:
                logger.debug(f"Syntax error: {error}")
        
        return fixed_lines
    
    def map_step_to_js(self, step: Step, previous_steps_js: List[str] = None, context: Dict[str, Any] = None, step_index: int = 0) -> List[str]:
        """
        Map a single step to JavaScript lines.
        
        Args:
            step: The step to map (Action or Check)
            previous_steps_js: List of JS lines from previous steps for context
            context: Additional context (page state, scenario info, etc.)
            
        Returns:
            List of JavaScript lines for this step
        """
        if not previous_steps_js:
            previous_steps_js = []
        if not context:
            context = {}
        
        # Prepare context for LLM
        llm_context = {
            'step_description': step.description,
            'step_type': step.__class__.__name__.lower(),
            'previous_steps_js': previous_steps_js,
            'context': context,
            'step_index': step_index,
            'step': step,  # Pass the step object for access to properties
            'page_state': context.get('page_state', 'No page state available'),
            'system_context': context.get('system_context', 'No system context available')
        }
        
        try:
            if isinstance(step, Action):
                return self._map_action_to_js(llm_context)
            elif isinstance(step, Check):
                return self._map_check_to_js(llm_context)
            elif isinstance(step, Precondition):
                return self._map_precondition_to_js(llm_context)
            else:
                logger.warning(f"Unknown step type: {type(step)}")
                return [f"// TODO: Implement {step.description}"]
                
        except Exception as e:
            logger.error(f"Failed to map step '{step.description}': {e}")
            return [f"// ERROR: Failed to map {step.description}"]
    
    def _map_action_to_js(self, context: Dict[str, Any]) -> List[str]:
        """Map an action step to JavaScript lines."""
        try:
            # Use action converter template
            template_path = 'targets/playwright/action_converter.j2'
            system_prompt = self.template_manager.render_template(template_path, **context)
            
            # Log the full prompt being sent to LLM
            logger.info("=== FULL PROMPT SENT TO LLM ===")
            logger.info(system_prompt)
            logger.info("=== END PROMPT ===")
            
            # Get LLM response
            response = self.llm_provider.generate(system_prompt, "")
            
            # Extract and clean JavaScript lines
            js_lines = self._extract_js_lines(response)
            
            logger.info(f"Mapped action '{context['step_description']}' to {len(js_lines)} JS lines")
            return js_lines
            
        except Exception as e:
            logger.error(f"Action mapping failed: {e}")
            return [f"// TODO: Implement action: {context['step_description']}"]
    
    def _map_check_to_js(self, context: Dict[str, Any]) -> List[str]:
        """Map a check step to JavaScript lines."""
        try:
            # Use check converter template
            template_path = 'targets/playwright/check_converter.j2'
            system_prompt = self.template_manager.render_template(template_path, **context)
            
            # Log the full prompt being sent to LLM
            logger.info("=== FULL PROMPT SENT TO LLM (CHECK) ===")
            logger.info(system_prompt)
            logger.info("=== END PROMPT ===")
            
            # Get LLM response
            response = self.llm_provider.generate(system_prompt, "")
            
            # Extract and clean JavaScript lines
            js_lines = self._extract_js_lines(response)
            
            logger.info(f"Mapped check '{context['step_description']}' to {len(js_lines)} JS lines")
            return js_lines
            
        except Exception as e:
            logger.error(f"Check mapping failed: {e}")
            return [f"// TODO: Implement check: {context['step_description']}"]
    
    def _map_precondition_to_js(self, context: Dict[str, Any]) -> List[str]:
        """Map a precondition step to JavaScript lines."""
        try:
            # Get the step object from context to access precondition properties
            step = context.get('step')
            if not step or not isinstance(step, Precondition):
                logger.error("Precondition step not found in context")
                return [f"// TODO: Implement precondition: {context['step_description']}"]
            
            # For login preconditions, try to use existing SDK functions first
            if step.precondition_type == 'login' and step.role:
                sdk_function_name = self._get_sdk_function_for_precondition(step)
                if sdk_function_name:
                    logger.info(f"Using SDK function for precondition: {sdk_function_name}")
                    return self._get_sdk_function_with_return(sdk_function_name, context)
            
            # Fallback to LLM generation for other precondition types
            template_context = {
                'description': step.description,
                'precondition_type': step.precondition_type,
                'role': step.role,
                'target': step.target,
                'step_description': step.description,
                'step_type': 'precondition',
                'available_scenarios': context.get('available_scenarios', [])
            }
            
            template_path = 'targets/playwright/precondition_converter.j2'
            system_prompt = self.template_manager.render_template(template_path, **template_context)
            
            # Get LLM response
            response = self.llm_provider.generate(system_prompt, "")
            logger.info(f"LLM response for precondition: {response[:200]}...")
            
            # Extract and clean JavaScript lines
            js_lines = self._extract_js_lines(response)
            
            logger.info(f"Mapped precondition '{context['step_description']}' to {len(js_lines)} JS lines")
            return js_lines
            
        except Exception as e:
            logger.error(f"Precondition mapping failed: {e}")
            return [f"// TODO: Implement precondition: {context['step_description']}"]
    
    def _get_sdk_function_for_precondition(self, precondition: Precondition) -> str:
        """Get the appropriate SDK function name for a precondition."""
        if precondition.precondition_type == 'login':
            if precondition.role == 'admin':
                return 'loginAsAdmin'
            elif precondition.role == 'user':
                return 'loginAsUser'
            else:
                return 'loginAsUser'  # Default fallback
        
        return None
    
    def _get_sdk_function_with_return(self, function_name: str, context: Dict[str, Any]) -> List[str]:
        """Get SDK function call with return value handling."""
        # Check if the function exists in SDK and has a return value
        sdk_function = context.get('sdk_manager', {}).get_function(function_name) if context.get('sdk_manager') else None
        
        if sdk_function and sdk_function.return_value and sdk_function.return_value != 'void':
            # Function returns a value, capture it
            return [f"const result = await sdk.{function_name}(page);"]
        else:
            # Function doesn't return a value, just call it
            return [f"await sdk.{function_name}(page);"]
    
    def _extract_js_lines(self, response: str) -> List[str]:
        """Extract JavaScript lines from LLM response without modification."""
        lines = response.strip().split('\n')
        js_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and markdown code blocks
            if line and not line.startswith('```') and not line.endswith('```'):
                js_lines.append(line)
        
        return js_lines
    
    def _validate_generated_code(self, js_lines: List[str]) -> List[str]:
        """Validate generated code using Node.js syntax checker."""
        try:
            from .node_syntax_checker import NodeSyntaxChecker
            
            validator = NodeSyntaxChecker()
            code_content = '\n'.join(js_lines)
            is_valid, errors = validator.check_syntax(code_content)
            
            if not is_valid:
                fixed_content, fixes_applied = validator.fix_syntax_errors(code_content)
                if fixes_applied > 0:
                    logger.info(f"Fixed {fixes_applied} syntax errors in generated code")
                    return fixed_content.split('\n')
                else:
                    logger.error(f"CRITICAL: Could not fix syntax errors: {errors}")
                    raise SyntaxError(f"Generated code has unfixable syntax errors: {errors}")
            else:
                return js_lines
        except Exception as e:
            logger.error(f"CRITICAL: Syntax validation failed: {e}")
            raise RuntimeError(f"Syntax validation failed: {e}") from e
    


class SpecComposer:
    """Composes complete specs from mapped steps using templates."""
    
    def __init__(self, template_manager):
        self.template_manager = template_manager
    
    def compose_spec(self, steps: List[Step], mapped_steps: List[Dict[str, Any]], scenario_name: str) -> str:
        """
        Compose a complete spec from mapped steps.
        
        Args:
            steps: Original step objects
            mapped_steps: List of dicts with 'description' and 'js_lines'
            scenario_name: Name of the scenario
            
        Returns:
            Complete JavaScript spec as string
        """
        # Generate scenario function name
        scenario_function_name = self._generate_scenario_function_name(scenario_name)
        
        # Prepare template context
        context = {
            'scenario_name': scenario_name,
            'scenario_function_name': scenario_function_name,
            'steps': mapped_steps,
            'functions': []  # For now, no separate functions - everything in main function
        }
        
        # Render the complete spec template
        template_path = 'targets/playwright/complete_spec.j2'
        return self.template_manager.render_template(template_path, **context)
    
    def _generate_scenario_function_name(self, scenario_name: str) -> str:
        """Generate a function name from scenario name."""
        # Convert scenario name to camelCase
        words = scenario_name.split('_')
        return words[0] + ''.join(word.capitalize() for word in words[1:])
