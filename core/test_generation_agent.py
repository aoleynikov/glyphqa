"""
Test Generation Agent - Intelligent orchestrator for test generation using existing tools.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StepType(Enum):
    ARRANGE = "arrange"
    ACT = "act"
    ASSERT = "assert"


@dataclass
class StepPlan:
    """Represents a planned step in the test generation process."""
    type: StepType
    description: str
    target: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    dependencies: List[str] = None
    expected_outcome: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class ScenarioPlan:
    """Represents the complete plan for a test scenario."""
    scenario_name: str
    scenario_text: str
    arrange_steps: List[StepPlan]
    act_steps: List[StepPlan]
    assert_steps: List[StepPlan]
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
    
    @property
    def all_steps(self) -> List[StepPlan]:
        """Get all steps in order: arrange, act, assert."""
        return self.arrange_steps + self.act_steps + self.assert_steps


class TestGenerationAgent:
    """
    Intelligent agent for test generation that uses existing tools.
    
    This agent analyzes scenarios, plans step sequences, and orchestrates
    the existing test generation infrastructure.
    """
    
    def __init__(self, scenario_builder):
        self.scenario_builder = scenario_builder
        self.llm_provider = scenario_builder.llm_provider
        self.template_manager = scenario_builder.template_manager
        self.debug_spec_manager = scenario_builder.debug_spec_manager
        self.step_mapper = scenario_builder.step_mapper
        self.sdk_manager = scenario_builder.sdk_manager
        self.filesystem = scenario_builder.filesystem

        # Initialize Modular SDK system
        from .generic_modular_sdk_manager import GenericModularSdkManager
        from .sdk_build_integration import SdkBuildIntegration
        
        # Create modular SDK manager
        from pathlib import Path
        self.modular_sdk_manager = GenericModularSdkManager(
            sdk_dir=Path('.glyph/sdk'),
            template_manager=self.template_manager,
            filesystem=self.filesystem,
            llm_provider=self.llm_provider
        )
        
        # Create SDK build integration
        self.sdk_integration = SdkBuildIntegration(
            modular_sdk_manager=self.modular_sdk_manager,
            template_manager=self.template_manager,
            llm_provider=self.llm_provider
        )
        
        # Keep legacy SDK agent for backward compatibility
        from .sdk_agent import SdkAgent
        self.sdk_agent = SdkAgent(
            sdk_manager=self.sdk_manager,
            template_manager=self.template_manager,
            filesystem=self.filesystem
        )
        
        # Initialize System Analysis Agent
        from .system_analysis_agent import SystemAnalysisAgent
        self.system_analysis_agent = SystemAnalysisAgent(
            llm_provider=self.llm_provider,
            template_manager=self.template_manager,
            filesystem=self.filesystem,
            config=scenario_builder.config
        )
        
    def analyze_scenario(self, scenario_name: str, scenario_text: str) -> ScenarioPlan:
        """
        Analyze a scenario and create a structured plan with arrange/act/assert steps.
        
        Args:
            scenario_name: Name of the scenario
            scenario_text: Raw scenario text from .glyph file
            
        Returns:
            ScenarioPlan with structured steps
        """
        logger.info(f"Analyzing scenario: {scenario_name}")
        
        # Use LLM to analyze the scenario and extract arrange/act/assert structure
        analysis_prompt = self._create_scenario_analysis_prompt(scenario_text)
        
        response = self.llm_provider.generate(analysis_prompt, scenario_text)
        plan_data = self._parse_analysis_response(response)
        
        # Create structured plan
        plan = ScenarioPlan(
            scenario_name=scenario_name,
            scenario_text=scenario_text,
            arrange_steps=[self._create_step_plan(step_data, StepType.ARRANGE) 
                          for step_data in plan_data.get('arrange', [])],
            act_steps=[self._create_step_plan(step_data, StepType.ACT) 
                      for step_data in plan_data.get('act', [])],
            assert_steps=[self._create_step_plan(step_data, StepType.ASSERT) 
                         for step_data in plan_data.get('assert', [])],
            dependencies=plan_data.get('dependencies', [])
        )
        
        logger.info(f"Created plan with {len(plan.arrange_steps)} arrange, "
                   f"{len(plan.act_steps)} act, {len(plan.assert_steps)} assert steps")
        
        return plan
    
    def analyze_scenario_dependencies(self, scenario_name: str, scenario_text: str) -> List[str]:
        """
        Analyze a scenario to extract its dependencies for topological sorting.
        
        Args:
            scenario_name: Name of the scenario
            scenario_text: Raw scenario text from .glyph file
            
        Returns:
            List of scenario names this scenario depends on
        """
        logger.info(f"Analyzing dependencies for scenario: {scenario_name}")
        
        # Get available SDK functions for dependency analysis
        available_functions = self.sdk_agent.get_available_functions()
        
        # Use LLM to analyze dependencies
        dependency_prompt = self._create_dependency_analysis_prompt(scenario_text, available_functions)
        
        response = self.llm_provider.generate(dependency_prompt, scenario_text)
        dependencies = self._parse_dependency_response(response, scenario_name)
        
        logger.info(f"Scenario {scenario_name} depends on: {dependencies}")
        return dependencies
    
    def get_sdk_info(self):
        """Get SDK information for other agents."""
        # Use modular SDK system
        try:
            return self.modular_sdk_manager.get_sdk_summary()
        except Exception as e:
            logger.warning(f"Failed to get modular SDK info, falling back to legacy: {e}")
            return self.sdk_agent.get_sdk_info()
    
    def validate_sdk_integrity(self) -> bool:
        """Validate SDK integrity."""
        # Use modular SDK system
        try:
            return self.modular_sdk_manager.validate_sdk_integrity()
        except Exception as e:
            logger.warning(f"Failed to validate modular SDK, falling back to legacy: {e}")
            return self.sdk_agent.validate_sdk_integrity()
    
    def rebuild_sdk(self) -> bool:
        """Rebuild the SDK from scratch."""
        # Use modular SDK system
        try:
            # Clear existing modules and regenerate
            self.modular_sdk_manager.modules.clear()
            return True
        except Exception as e:
            logger.warning(f"Failed to rebuild modular SDK, falling back to legacy: {e}")
            return self.sdk_agent.rebuild_sdk()
    
    def get_sdk_context_for_builder(self, scenario_name: str, current_step: str, 
                                   accumulated_steps: List[str] = None) -> str:
        """Get SDK context for the builder using modular system."""
        try:
            return self.sdk_integration.provide_sdk_context_to_builder(
                scenario_name=scenario_name,
                current_step=current_step,
                accumulated_steps=accumulated_steps
            )
        except Exception as e:
            logger.warning(f"Failed to get modular SDK context, falling back to legacy: {e}")
            # Fallback to legacy system
            return self.system_analysis_agent.get_context_for_builder(current_step, accumulated_steps)
    
    def _create_scenario_analysis_prompt(self, scenario_text: str) -> str:
        """Create the system prompt for scenario analysis."""
        return self.template_manager.render_template('agent/scenario_analysis.j2')
    
    def _create_dependency_analysis_prompt(self, scenario_text: str, available_functions: List[str] = None) -> str:
        """Create the system prompt for dependency analysis."""
        if available_functions is None:
            available_functions = []
        
        return self.template_manager.render_template(
            'agent/dependency_analysis.j2',
            available_functions=available_functions
        )
    
    def _parse_dependency_response(self, response: str, scenario_name: str) -> List[str]:
        """Parse the LLM response into a list of dependencies."""
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.strip()
        
        try:
            dependencies = json.loads(json_str)
            if isinstance(dependencies, list):
                # Filter out self-references and invalid dependencies
                valid_dependencies = []
                for dep in dependencies:
                    if dep != scenario_name:  # Remove self-references
                        valid_dependencies.append(dep)
                return valid_dependencies
            else:
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dependency response: {e}")
            logger.error(f"Response: {response}")
            return []
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis response: {e}")
            logger.error(f"Response: {response}")
            raise
    
    def _create_step_plan(self, step_data: Dict[str, Any], step_type: StepType) -> StepPlan:
        """Create a StepPlan from parsed data."""
        return StepPlan(
            type=step_type,
            description=step_data.get('description', ''),
            target=step_data.get('target'),
            data=step_data.get('data'),
            expected_outcome=step_data.get('expected_outcome')
        )
    
    def _create_fallback_plan(self, scenario_name: str, scenario_text: str) -> ScenarioPlan:
        """Create a simple fallback plan when analysis fails."""
        logger.warning(f"Using fallback plan for {scenario_name}")
        
        # Simple heuristic: treat each line as an action
        lines = [line.strip() for line in scenario_text.split('\n') if line.strip()]
        
        act_steps = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['should', 'verify', 'check', 'expect']):
                # This looks like an assertion
                continue
            act_steps.append(StepPlan(
                type=StepType.ACT,
                description=line
            ))
        
        # Add basic assertions
        assert_steps = [
            StepPlan(type=StepType.ASSERT, description="no console errors"),
            StepPlan(type=StepType.ASSERT, description="page loaded successfully")
        ]
        
        return ScenarioPlan(
            scenario_name=scenario_name,
            scenario_text=scenario_text,
            arrange_steps=[],
            act_steps=act_steps,
            assert_steps=assert_steps
        )
    
    def build_scenario_step_by_step(self, scenario_name: str, scenario_text: str) -> str:
        """
        Build a complete test scenario using step-by-step approach with agent intelligence.
        
        Args:
            scenario_name: Name of the scenario
            scenario_text: Raw scenario text
            
        Returns:
            Complete Playwright test spec as string
        """
        logger.info(f"Building scenario step-by-step: {scenario_name}")
        
        # Start the iterative build process
        self.system_analysis_agent.start_scenario(scenario_name)
        
        # Analyze scenario and create plan
        plan = self.analyze_scenario(scenario_name, scenario_text)
        
        # Build steps incrementally with iterative system analysis
        all_js_lines = []
        
        # Process arrange steps
        for i, step_plan in enumerate(plan.arrange_steps):
            logger.info(f"Building arrange step {i+1}: {step_plan.description}")
            
            # Capture page state using System Analysis Agent (with all previous steps)
            page_state = self.system_analysis_agent.capture_page_state(
                step_plan.description, 
                f"Arrange step {i+1}: {step_plan.description}"
            )
            
            # Build step with captured page state
            js_lines, _ = self._build_step_with_context(
                step_plan, all_js_lines, f"Page state: {page_state.context}", f"arrange_{i}"
            )
            all_js_lines.extend(js_lines)
            
            # Add the step to accumulated steps for next iteration
            if js_lines:
                js_code = '\n'.join(js_lines)
                self.system_analysis_agent.add_step(step_plan.description, js_code)
                
                # REFLECTION STEP: Capture page state after this step is executed
                # This ensures we have fresh context for the next step
                reflection_page_state = self.system_analysis_agent.capture_page_state(
                    f"After executing: {step_plan.description}",
                    f"Reflection after {step_plan.description}"
                )
                from .build_output_manager import build_output
                build_output.reflection_step(len(reflection_page_state.elements), step_plan.description)
        
        # Process act steps  
        for i, step_plan in enumerate(plan.act_steps):
            logger.info(f"Building act step {i+1}: {step_plan.description}")
            
            # Capture page state using System Analysis Agent (with all previous steps)
            page_state = self.system_analysis_agent.capture_page_state(
                step_plan.description, 
                f"Act step {i+1}: {step_plan.description}"
            )
            
            # Build step with captured page state
            js_lines, _ = self._build_step_with_context(
                step_plan, all_js_lines, f"Page state: {page_state.context}", f"act_{i}"
            )
            all_js_lines.extend(js_lines)
            
            # Add the step to accumulated steps for next iteration
            if js_lines:
                js_code = '\n'.join(js_lines)
                self.system_analysis_agent.add_step(step_plan.description, js_code)
                
                # REFLECTION STEP: Capture page state after this step is executed
                # This ensures we have fresh context for the next step
                reflection_page_state = self.system_analysis_agent.capture_page_state(
                    f"After executing: {step_plan.description}",
                    f"Reflection after {step_plan.description}"
                )
                from .build_output_manager import build_output
                build_output.reflection_step(len(reflection_page_state.elements), step_plan.description)
        
        # Process assert steps
        for i, step_plan in enumerate(plan.assert_steps):
            logger.info(f"Building assert step {i+1}: {step_plan.description}")
            
            # Capture page state using System Analysis Agent (with all previous steps)
            page_state = self.system_analysis_agent.capture_page_state(
                step_plan.description, 
                f"Assert step {i+1}: {step_plan.description}"
            )
            
            # Build step with captured page state
            js_lines, _ = self._build_step_with_context(
                step_plan, all_js_lines, f"Page state: {page_state.context}", f"assert_{i}"
            )
            all_js_lines.extend(js_lines)
            
            # REFLECTION STEP: Capture page state after this step is executed
            # This ensures we have fresh context for the next step
            reflection_page_state = self.system_analysis_agent.capture_page_state(
                f"After executing: {step_plan.description}",
                f"Reflection after {step_plan.description}"
            )
            print(f"REFLECTION: Captured {len(reflection_page_state.elements)} elements after step: {step_plan.description}")
        
        # Compose final spec
        complete_spec = self._compose_final_spec(all_js_lines, scenario_name)
        
        # Update SDK with the implemented scenario function
        self._update_sdk_with_scenario(scenario_name, complete_spec)
        
        return complete_spec
    
    def _build_step_with_context(self, step_plan: StepPlan, previous_js_lines: List[str], 
                                current_page_state: str, step_identifier: str) -> tuple[List[str], str]:
        """
        Build a single step with page context awareness.
        
        Returns:
            Tuple of (js_lines, updated_page_state)
        """
        # Proactively gather context from system analysis agent if needed
        system_context = self.system_analysis_agent.get_context_for_builder(
            step_plan.description, 
            self.system_analysis_agent.accumulated_steps
        )
        
        # Create context for step mapping
        context = {
            'scenario_name': step_plan.description,
            'scenario_description': step_plan.description,
            'page_state': current_page_state,
            'previous_steps_js': previous_js_lines,
            'sdk_manager': self.sdk_manager,
            'step_plan': step_plan,  # Pass the plan for agent context
            'system_context': system_context  # Add system analysis context
        }
        
        # Use existing step mapper but with agent context
        if step_plan.type == StepType.ASSERT:
            from core.steps import Check
            step = Check(step_plan.description, 'visibility')
        else:
            from core.steps import Action
            step = Action(step_plan.description, 'click')
        
        # Map step to JavaScript
        js_lines = self.step_mapper.map_step_to_js(step, previous_js_lines, context, 0)
        
        # Use System Analysis Agent to capture page state and correct selectors
        try:
            # Filter out check steps from actions (use existing logic)
            action_steps_js = [line for line in previous_js_lines + js_lines 
                             if not any(check_indicator in line for check_indicator in 
                                      ['expect(', 'toBeVisible', 'toHaveText', 'toContainText'])]
            
            # Capture page state using System Analysis Agent
            page_state = self.system_analysis_agent.capture_page_state(
                step_plan.description, 
                f"Step: {step_plan.description}"
            )
            
            # JS lines are not modified - they come directly from LLM and templates
            
            # Validate step result
            if not self._validate_step_result(js_lines, page_state, step_plan):
                logger.warning(f"Step validation failed for {step_plan.description}, attempting to fix")
                js_lines = self._debug_and_fix_step_with_system_analysis(js_lines, page_state, step_plan)
            
            return js_lines, f"Page state captured: {len(page_state.elements)} elements found"
            
        except Exception as e:
            logger.error(f"Failed to capture page state for {step_identifier}: {e}")
            return js_lines, current_page_state
    
    def _convert_js_lines_to_spec(self, js_lines: List[str]) -> str:
        """Convert JS lines to a debug spec using template."""
        # Check if any of the js_lines already contain page.goto('/')
        has_initial_navigation = any('page.goto(\'/\')' in line for line in js_lines)
        
        return self.template_manager.render_template(
            'agent/debug_spec.j2',
            js_lines=js_lines,
            has_initial_navigation=has_initial_navigation
        )
    
    def _validate_step_result(self, js_lines: List[str], page_state, step_plan: StepPlan) -> bool:
        """Validate if the step result matches expectations."""
        # Basic validation - check if page state was captured successfully
        if hasattr(page_state, 'elements'):
            # PageState object
            if len(page_state.elements) == 0:
                return False
        else:
            # String page state (legacy)
            if len(page_state) < 100:  # Likely an error message
                return False
        
        # Could add more sophisticated validation here
        return True
    
    def _debug_and_fix_step_with_system_analysis(self, js_lines: List[str], page_state, step_plan: StepPlan) -> List[str]:
        """Debug and fix a step using System Analysis Agent."""
        logger.info(f"Debugging step with system analysis: {step_plan.description}")
        
        # Return JS lines as-is without modification
        return js_lines
    
    
    
    
    
    def _create_selector_from_element(self, element: dict) -> str:
        """Create a Playwright selector from element data."""
        tag = element.get('tag', '')
        text_content = element.get('textContent', '').strip()
        element_id = element.get('id', '')
        class_name = element.get('className', '')
        
        # Prefer ID if available
        if element_id:
            return f'#{element_id}'
        
        # Use text content with appropriate tag
        if text_content:
            return f'{tag}:has-text(\'{text_content}\')'
        
        # Fallback to class
        if class_name:
            return f'.{class_name.split()[0]}'  # Use first class
        
        return tag
    
    def _compose_final_spec(self, all_js_lines: List[str], scenario_name: str) -> str:
        """Compose the final test spec from all JS lines."""
        # Use existing spec composer logic from step_mapper
        from core.step_mapper import SpecComposer
        spec_composer = SpecComposer(self.template_manager)
        
        # Create mock mapped steps for the composer
        mapped_steps = []
        for i, js_line in enumerate(all_js_lines):
            mapped_steps.append({
                'description': f'Step {i+1}',
                'js_lines': [js_line],
                'type': 'action'
            })
        
        return spec_composer.compose_spec([], mapped_steps, scenario_name)
    
    def _update_sdk_with_scenario(self, scenario_name: str, spec_content: str):
        """Update SDK with the implemented scenario function for reuse."""
        try:
            # Extract the main scenario function from the spec
            scenario_function = self._extract_scenario_function(spec_content, scenario_name)
            
            if scenario_function:
                # Create SDK update request
                from .sdk_agent import SdkUpdateRequest
                
                request = SdkUpdateRequest(
                    scenario_name=scenario_name,
                    function_name=scenario_function['name'],
                    function_content=scenario_function['content'],
                    function_type="scenario",
                    summary=f"Complete scenario implementation for {scenario_name}"
                )
                
                # Use modular SDK system to add the function
                function_data = {
                    'name': scenario_function['name'],
                    'content': scenario_function['content'],
                    'summary': request.summary,
                    'type': request.function_type,
                    'dependencies': request.dependencies
                }
                
                success = self.modular_sdk_manager.add_function(function_data)
                
                if success:
                    logger.info(f"✅ Added scenario function '{scenario_function['name']}' to modular SDK")
                else:
                    logger.error(f"Failed to add scenario function '{scenario_function['name']}' to modular SDK")
                    
                    # Fallback to legacy SDK agent
                    success = self.sdk_agent.add_scenario_function(request)
                    if success:
                        logger.info(f"✅ Added scenario function '{scenario_function['name']}' to legacy SDK")
                    else:
                        logger.error(f"Failed to add scenario function '{scenario_function['name']}' to legacy SDK")
            else:
                logger.warning(f"Could not extract scenario function from {scenario_name}")
            
            # Also extract and add reusable functions
            reusable_functions = self._extract_reusable_functions(spec_content, scenario_name)
            
            for func in reusable_functions:
                try:
                    request = SdkUpdateRequest(
                        scenario_name=scenario_name,
                        function_name=func['name'],
                        function_content=func['content'],
                        function_type="reusable",
                        summary=f"Reusable function for {func['name']}"
                    )
                    
                    # Use modular SDK system to add the function
                    function_data = {
                        'name': func['name'],
                        'content': func['content'],
                        'summary': request.summary,
                        'type': request.function_type,
                        'dependencies': request.dependencies
                    }
                    
                    success = self.modular_sdk_manager.add_function(function_data)
                    
                    if success:
                        logger.info(f"✅ Added reusable function '{func['name']}' to modular SDK")
                    else:
                        logger.error(f"Failed to add reusable function '{func['name']}' to modular SDK")
                        
                        # Fallback to legacy SDK agent
                        success = self.sdk_agent.add_scenario_function(request)
                        if success:
                            logger.info(f"✅ Added reusable function '{func['name']}' to legacy SDK")
                        else:
                            logger.error(f"Failed to add reusable function '{func['name']}' to legacy SDK")
                        
                except Exception as e:
                    logger.error(f"Failed to add reusable function '{func['name']}': {e}")
                
        except Exception as e:
            logger.error(f"Failed to update SDK with scenario {scenario_name}: {e}")
        
        # Run syntax fixer after SDK updates
        self._fix_sdk_syntax()
    
    def _extract_scenario_function(self, spec_content: str, scenario_name: str) -> Optional[Dict[str, str]]:
        """Extract the main scenario function from the spec content using LLM."""
        logger.info(f"Extracting function for scenario: {scenario_name}")
        
        # Use LLM to extract the function
        extraction_prompt = self.template_manager.render_template(
            'agent/function_extractor.j2',
            spec_content=spec_content,
            scenario_name=scenario_name,
            system_analysis_agent=self.system_analysis_agent
        )
        
        response = self.llm_provider.generate(extraction_prompt, spec_content)
        function_data = self._parse_function_extraction_response(response)
        
        if function_data:
            # Validate extracted function against constraints
            function_data = self._validate_extracted_function(function_data, spec_content)
            logger.info(f"Successfully extracted function: {function_data['name']}")
            return function_data
        else:
            logger.warning(f"Failed to extract function from spec")
            return None
    
    def _extract_reusable_functions(self, spec_content: str, scenario_name: str) -> List[Dict[str, str]]:
        """Extract reusable functions from the spec content using LLM."""
        logger.info(f"Extracting reusable functions for scenario: {scenario_name}")
        
        # Use LLM to extract the functions
        extraction_prompt = self.template_manager.render_template(
            'agent/function_extractor.j2',
            spec_content=spec_content,
            scenario_name=scenario_name,
            system_analysis_agent=self.system_analysis_agent
        )
        
        response = self.llm_provider.generate(extraction_prompt, spec_content)
        function_data = self._parse_reusable_functions_response(response)
        
        if function_data:
            logger.info(f"Successfully extracted {len(function_data)} reusable functions")
            return function_data
        else:
            logger.warning(f"Failed to extract reusable functions from spec")
            return []
    
    def _validate_extracted_function(self, function_data: Dict[str, str], spec_content: str) -> Dict[str, str]:
        """Validate extracted function against constraint rules."""
        import re
        
        function_content = function_data.get('content', '')
        
        # Check for forbidden selectors
        forbidden_patterns = [
            r'#\w+',  # ID selectors
            r'\[data-testid="[^"]*"\]',  # data-testid selectors
            r'input\[name="email"\]',  # Made-up selectors
        ]
        
        validated_content = function_content
        for pattern in forbidden_patterns:
            if re.search(pattern, validated_content):
                logger.warning(f"Found forbidden selector in function: {function_data['name']}")
                # Try to correct common patterns
                validated_content = self._correct_function_selectors(validated_content, spec_content)
        
        # Update the function data with validated content
        function_data['content'] = validated_content
        return function_data
    
    def _correct_function_selectors(self, function_content: str, spec_content: str) -> str:
        """Attempt to correct forbidden selectors in function content."""
        corrected_content = function_content
        
        # Common corrections
        corrections = [
            ('#username', 'input[type="text"]'),
            ('#password', 'input[type="password"]'),
            ('#loginButton', 'button[type="submit"]'),
            ('#logoutButton', 'text="Logout"'),
            ('#submit', 'button[type="submit"]'),
        ]
        
        for forbidden, allowed in corrections:
            if forbidden in corrected_content and allowed in spec_content:
                corrected_content = corrected_content.replace(forbidden, allowed)
                logger.info(f"Corrected selector: {forbidden} -> {allowed}")
        
        return corrected_content
    
    def _parse_function_extraction_response(self, response: str) -> Optional[Dict[str, str]]:
        """Parse the LLM response for function extraction."""
        try:
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            function_data = json.loads(json_str)
            
            # Handle new structure with main_function and reusable_functions
            if 'main_function' in function_data:
                main_func = function_data['main_function']
                if 'name' in main_func and 'code' in main_func:
                    return {
                        'name': main_func['name'],
                        'content': main_func['code']
                    }
            
            # Handle legacy structure
            if 'name' in function_data and 'content' in function_data:
                return {
                    'name': function_data['name'],
                    'content': function_data['content']
                }
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse function extraction response: {e}")
            logger.error(f"Response: {response}")
            return None
    
    def _parse_reusable_functions_response(self, response: str) -> List[Dict[str, str]]:
        """Parse the LLM response for reusable function extraction."""
        try:
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            function_data = json.loads(json_str)
            
            # Handle new structure with reusable_functions
            if 'reusable_functions' in function_data:
                reusable_funcs = function_data['reusable_functions']
                if isinstance(reusable_funcs, list):
                    return [
                        {
                            'name': func['name'],
                            'content': func['code']
                        }
                        for func in reusable_funcs
                        if 'name' in func and 'code' in func
                    ]
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reusable functions response: {e}")
            logger.error(f"Response: {response}")
            return []
    
    def _fix_sdk_syntax(self) -> None:
        """Run Node.js-based syntax fixer on the SDK files."""
        try:
            import os
            from .node_syntax_checker import NodeSyntaxChecker
            checker = NodeSyntaxChecker()
            
            # Fix main SDK file
            sdk_file = '.glyph/sdk.js'
            if os.path.exists(sdk_file):
                is_valid, errors = checker.check_file(sdk_file)
                if not is_valid:
                    with open(sdk_file, 'r') as f:
                        content = f.read()
                    fixed_content, fixes_applied = checker.fix_syntax_errors(content)
                    if fixes_applied > 0:
                        with open(sdk_file, 'w') as f:
                            f.write(fixed_content)
                        logger.info(f"🔧 Fixed {fixes_applied} syntax errors in SDK")
                        
        except Exception as e:
            logger.warning(f"Failed to run Node.js syntax fixer: {e}")
