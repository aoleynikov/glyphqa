from typing import List, Optional, Dict, TYPE_CHECKING
from pathlib import Path
import logging
import json
import re
import os
from .exceptions import BuildError, GuideError, FileSystemError, LLMError
from .constants import Constants
from .models import Scenario, Guide

if TYPE_CHECKING:
    from .models import Scenario, Guide

logger = logging.getLogger(__name__)


class ActionConverter:
    """Handles conversion of human-readable actions to Playwright code."""
    
    def __init__(self, llm_provider, template_manager, target):
        self.llm_provider = llm_provider
        self.template_manager = template_manager
        self.target = target
    
    def convert_action_to_playwright(self, action: str, previous_actions: List[str] = None, system_insights: str = None, page_dump: str = None) -> str:
        """Convert a human-readable action description to Playwright code using LLM."""
        if not previous_actions:
            previous_actions = []
        if not system_insights:
            system_insights = "No system insights available"
        
        # Use actual page state if available, otherwise fallback
        current_page_state = page_dump if page_dump else "No page state available"
        
        # Prepare context for the LLM
        context = {
            'action': action,
            'previous_actions': previous_actions,
            'system_insights': system_insights,
            'current_page_state': current_page_state
        }
        
        # Use LLM to convert action to Playwright code
        try:
            template_path = self.target.get_template_path('action_converter')
            logger.info(f"Using template: {template_path}")
            prompt = self.template_manager.render_template(template_path, **context)
            logger.info(f"Generated prompt length: {len(prompt)}")
            
            response = self.llm_provider.generate(prompt, action)
            logger.info(f"LLM response length: {len(response)}")
            
            # Clean up the response to extract just the Playwright code
            lines = response.split('\n')
            playwright_code = []
            in_code_block = False
            
            for line in lines:
                if '```javascript' in line or '```js' in line:
                    in_code_block = True
                    continue
                elif '```' in line and in_code_block:
                    in_code_block = False
                    break
                elif in_code_block and line.strip():
                    playwright_code.append(line)
                elif line.strip().startswith('await page.') or line.strip().startswith('page.'):
                    # Also capture standalone Playwright lines outside code blocks
                    playwright_code.append(line.strip())
            
            logger.info(f"Extracted {len(playwright_code)} lines of Playwright code")
            if playwright_code:
                result = '\n    '.join(playwright_code)
                logger.info(f"Final result: {result}")
                return result
            else:
                logger.info("No Playwright code extracted, using fallback")
                # Fallback to a simple approach if LLM doesn't generate proper code
                return self._fallback_action_conversion(action)
                
        except Exception as e:
            logger.warning(f"LLM action conversion failed: {e}, falling back to heuristic approach")
            return self._fallback_action_conversion(action)
    
    def _fallback_action_conversion(self, action: str) -> str:
        """Fallback action conversion using simple heuristics."""
        action_lower = action.lower()
        
        if 'click' in action_lower:
            if 'button' in action_lower:
                return 'await page.click("button")'
            elif 'link' in action_lower:
                return 'await page.click("a")'
            else:
                return 'await page.click("button")'
        elif 'fill' in action_lower or 'enter' in action_lower:
            if 'username' in action_lower:
                return 'await page.fill("input[name=\\"username\\"]", "test_user")'
            elif 'password' in action_lower:
                return 'await page.fill("input[name=\\"password\\"]", "test_password")'
            elif 'email' in action_lower:
                return 'await page.fill("input[name=\\"email\\"]", "test@example.com")'
            else:
                return 'await page.fill("input", "test_value")'
        elif 'navigate' in action_lower or 'go to' in action_lower:
            return 'await page.goto("/")'
        elif 'submit' in action_lower:
            return 'await page.click("button[type=\\"submit\\"]")'
        elif 'select' in action_lower:
            return 'await page.selectOption("select", "option_value")'
        elif 'wait' in action_lower:
            return 'await page.waitForTimeout(1000)'
        else:
            return f'// TODO: Implement action: {action}'


class SpecGenerator:
    """Handles generation and management of test specifications."""
    
    def __init__(self, template_manager, target, filesystem):
        self.template_manager = template_manager
        self.target = target
        self.filesystem = filesystem
    
    def generate_initial_spec(self) -> str:
        """Generate the initial test specification."""
        template_path = self.target.get_template_path('initial_spec')
        initial_system_prompt = self.template_manager.render_template(template_path)
        
        # The template is just instructions - we need to call the LLM to generate the actual spec
        # For now, let's create a simple initial spec with navigation to root
        initial_spec = '''import { test, expect } from '@playwright/test';

async function navigateToRoot(page) {
    await page.goto('/');
}

test.describe('Initial Test', () => {
    test('should navigate to root', async ({ page }) => {
        await navigateToRoot(page);
    });
});

export { navigateToRoot };'''
        
        return initial_spec
    
    def build_complete_spec_with_actions(self, current_spec: str, implemented_actions: List[str], new_action_code: str, action: str, scenario: 'Scenario') -> str:
        """Build a complete new spec with all actions including the new one."""
        logger.info(f"DEBUG: build_complete_spec_with_actions called with:")
        logger.info(f"DEBUG: - current_spec length: {len(current_spec)}")
        logger.info(f"DEBUG: - implemented_actions: {implemented_actions}")
        logger.info(f"DEBUG: - new_action_code: {new_action_code}")
        logger.info(f"DEBUG: - action: {action}")
        logger.info(f"DEBUG: - scenario.name: {scenario.name}")
        
        # Extract existing functions and structure from current spec
        lines = current_spec.split('\n')
        imports = []
        functions = []
        current_function = []
        in_function = False
        
        for line in lines:
            # Capture import statements
            if line.strip().startswith('import '):
                imports.append(line)
                continue
                
            # Capture function definitions
            if line.strip().startswith('async function ') or line.strip().startswith('function '):
                if current_function:
                    functions.append('\n'.join(current_function))
                current_function = [line]
                in_function = True
            elif in_function and line.strip() == '}':
                current_function.append(line)
                in_function = False
            elif in_function:
                current_function.append(line)
        
        if current_function:
            functions.append('\n'.join(current_function))
        
        # Generate a unique action function name based on the action description
        # Let the LLM generate a descriptive name for this specific action
        action_name = self._generate_action_function_name(action)
        logger.info(f"DEBUG: Generated action_name: {action_name}")
        new_function = f'''async function {action_name}(page) {{
    {new_action_code}
}}'''
        logger.info(f"DEBUG: Created new_function: {new_function}")
        
        # Add the new function to the list
        functions.append(new_function)
        logger.info(f"DEBUG: Total functions after adding new one: {len(functions)}")
        
        # Build the main scenario function that orchestrates all actions
        main_scenario_function_name = self._generate_scenario_function_name(scenario)
        logger.info(f"DEBUG: Generated main scenario function name: {main_scenario_function_name}")
        
        # Extract function names from existing functions (excluding the main scenario function)
        action_function_names = []
        logger.info(f"DEBUG: Extracting function names from {len(functions)} functions:")
        for i, func in enumerate(functions):
            # Extract function name from function definition
            if 'async function ' in func:
                func_name = func.split('async function ')[1].split('(')[0].strip()
                action_function_names.append(func_name)
                logger.info(f"DEBUG: Function {i}: extracted name '{func_name}'")
            elif 'function ' in func:
                func_name = func.split('function ')[1].split('(')[0].strip()
                action_function_names.append(func_name)
                logger.info(f"DEBUG: Function {i}: extracted name '{func_name}'")
        
        # Create the main scenario function that calls all action functions
        main_function_calls = []
        for func_name in action_function_names:
            main_function_calls.append(f'    await {func_name}(page)')
        
        main_function_calls_text = '\n'.join(main_function_calls)
        
        main_scenario_function = f'''async function {main_scenario_function_name}(page) {{
{main_function_calls_text}
}}'''
        
        # Add the main scenario function
        functions.append(main_scenario_function)
        
        # Build test calls - only call the main scenario function
        test_calls = [f'        await {main_scenario_function_name}(page)']
        
        test_calls_text = '\n'.join(test_calls)
        
        # Build export statement - export the main scenario function and all action functions
        all_function_names = action_function_names + [main_scenario_function_name]
        export_names = ', '.join(all_function_names)
        
        # Get scenario information for dynamic naming
        scenario_name = scenario.name.replace('_', ' ').title()
        scenario_description = "complete the workflow"
        
        test_content = f'''test.describe('{scenario_name}', () => {{
    test('should {scenario_description}', async ({{ page }}) => {{
{test_calls_text}
    }});
}});

export {{ {export_names} }};'''
        
        # Combine everything into a complete new spec
        return '\n\n'.join(imports) + '\n\n' + '\n\n'.join(functions) + '\n\n' + test_content
    
    def build_complete_spec_from_actions(self, action_functions: List[str], scenario: 'Scenario') -> str:
        """Build a complete spec from collected action functions."""
        logger.info(f"DEBUG: build_complete_spec_from_actions called with {len(action_functions)} action functions")
        
        # Get the main scenario function name
        main_scenario_function_name = self._generate_scenario_function_name(scenario)
        logger.info(f"DEBUG: Generated main scenario function name: {main_scenario_function_name}")
        
        # Extract function names from action functions
        action_function_names = []
        for i, func in enumerate(action_functions):
            if 'async function ' in func:
                func_name = func.split('async function ')[1].split('(')[0].strip()
                action_function_names.append(func_name)
                logger.info(f"DEBUG: Action function {i}: extracted name '{func_name}'")
        
        # Create the main scenario function that calls all action functions
        main_function_calls = []
        for func_name in action_function_names:
            main_function_calls.append(f'    await {func_name}(page)')
        
        main_function_calls_text = '\n'.join(main_function_calls)
        
        main_scenario_function = f'''async function {main_scenario_function_name}(page) {{
{main_function_calls_text}
}}'''
        
        # Combine all functions
        all_functions = action_functions + [main_scenario_function]
        
        # Build test calls - only call the main scenario function
        test_calls = [f'        await {main_scenario_function_name}(page)']
        test_calls_text = '\n'.join(test_calls)
        
        # Build export statement - export the main scenario function and all action functions
        all_function_names = action_function_names + [main_scenario_function_name]
        export_names = ', '.join(all_function_names)
        
        # Get scenario information for dynamic naming
        scenario_name = scenario.name.replace('_', ' ').title()
        scenario_description = "complete the workflow"
        
        # Add the required Playwright imports
        imports = '''import { test, expect } from '@playwright/test';'''
        
        test_content = f'''test.describe('{scenario_name}', () => {{
    test('should {scenario_description}', async ({{ page }}) => {{
{test_calls_text}
    }});
}});

export {{ {export_names} }};'''
        
        # Combine everything into a complete new spec
        return imports + '\n\n' + '\n\n'.join(all_functions) + '\n\n' + test_content
    
    def build_complete_spec_from_actions_and_references(self, action_functions: List[str], reference_functions: dict, scenario: 'Scenario') -> str:
        """Build a complete spec from collected action functions and reference functions."""
        logger.info(f"DEBUG: build_complete_spec_from_actions_and_references called with {len(action_functions)} action functions and {len(reference_functions)} reference functions")
        
        # Get the main scenario function name
        main_scenario_function_name = self._generate_scenario_function_name(scenario)
        logger.info(f"DEBUG: Generated main scenario function name: {main_scenario_function_name}")
        
        # Extract function names from action functions
        action_function_names = []
        for i, func in enumerate(action_functions):
            if 'async function ' in func:
                func_name = func.split('async function ')[1].split('(')[0].strip()
                action_function_names.append(func_name)
                logger.info(f"DEBUG: Action function {i}: extracted name '{func_name}'")
        
        # Get reference function names
        reference_function_names = list(reference_functions.keys())
        logger.info(f"DEBUG: Reference function names: {reference_function_names}")
        
        # Create the main scenario function that calls all functions in order
        main_function_calls = []
        
        # First, always navigate to root
        main_function_calls.append('    await page.goto(\'/\')')
        logger.info(f"DEBUG: Added navigation to root")
        
        # Then, call the main reference function (e.g., loginAsAdmin)
        if reference_function_names:
            # Find the main scenario function from references (usually the last one exported)
            main_ref_function = None
            for ref_name in reference_function_names:
                if ref_name.lower().replace('_', '') in scenario.name.lower().replace('_', ''):
                    main_ref_function = ref_name
                    break
            if not main_ref_function and reference_function_names:
                main_ref_function = reference_function_names[-1]  # Use the last one as fallback
            
            if main_ref_function:
                main_function_calls.append(f'    await {main_ref_function}(page)')
                logger.info(f"DEBUG: Added reference function call: {main_ref_function}")
        
        # Then call all action functions
        for func_name in action_function_names:
            main_function_calls.append(f'    await {func_name}(page)')
        
        main_function_calls_text = '\n'.join(main_function_calls)
        
        main_scenario_function = f'''async function {main_scenario_function_name}(page) {{
{main_function_calls_text}
}}'''
        
        # Combine all functions: reference functions first, then action functions, then main function
        all_functions = list(reference_functions.values()) + action_functions + [main_scenario_function]
        
        # Build test calls - only call the main scenario function
        test_calls = [f'        await {main_scenario_function_name}(page)']
        test_calls_text = '\n'.join(test_calls)
        
        # Build export statement - export the main scenario function and all other functions
        all_function_names = reference_function_names + action_function_names + [main_scenario_function_name]
        export_names = ', '.join(all_function_names)
        
        # Get scenario information for dynamic naming
        scenario_name = scenario.name.replace('_', ' ').title()
        scenario_description = "complete the workflow"
        
        # Add the required Playwright imports
        imports = '''import { test, expect } from '@playwright/test';'''
        
        test_content = f'''test.describe('{scenario_name}', () => {{
    test('should {scenario_description}', async ({{ page }}) => {{
{test_calls_text}
    }});
}});

export {{ {export_names} }};'''
        
        # Combine everything into a complete new spec
        return imports + '\n\n' + '\n\n'.join(all_functions) + '\n\n' + test_content
    
    def save_spec(self, spec_file: str, spec_content: str):
        """Save the final spec to file."""
        self.filesystem.write_text(spec_file, spec_content)
    
    def _generate_action_function_name(self, action: str) -> str:
        """Generate a unique function name for an individual action based on its description."""
        # Convert action description to a camelCase function name
        # Remove common words and convert to camelCase
        words = action.lower().split()
        
        # Filter out common words that don't add meaning
        filtered_words = []
        for word in words:
            if word not in ['the', 'a', 'an', 'and', 'or', 'to', 'in', 'on', 'at', 'by', 'for', 'with', 'from']:
                filtered_words.append(word)
        
        if not filtered_words:
            # Fallback: use first few words
            filtered_words = words[:3]
        
        # Convert to camelCase
        function_name = filtered_words[0]
        for word in filtered_words[1:]:
            function_name += word.capitalize()
        
        # Ensure it's a valid JavaScript identifier
        function_name = re.sub(r'[^a-zA-Z0-9_]', '', function_name)
        
        # Ensure it starts with a letter
        if function_name and not function_name[0].isalpha():
            function_name = 'action' + function_name
        
        return function_name
    
    def _generate_scenario_function_name(self, scenario: 'Scenario') -> str:
        """Generate a function name for the main scenario function from the glyph file path."""
        # Get the glyph file path relative to scenarios directory
        # scenario.name is the filename without extension (e.g., 'create_user')
        # Split on both _ and / to handle nested paths
        path_parts = re.split(r'[_\//]', scenario.name)
        
        # Convert to camelCase
        function_name = path_parts[0]
        for part in path_parts[1:]:
            function_name += part.capitalize()
        
        return function_name


class DebugSpecManager:
    """Handles generation of debug specs and page state capture."""
    
    def __init__(self, target, template_manager):
        self.target = target
        self.template_manager = template_manager
    
    def generate_debug_spec(self, current_spec: str, current_action: str = None) -> str:
        """Generate a debug specification for capturing page state."""
        lines = current_spec.split('\n')
        implemented_actions = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('await page.') and not line.startswith('await page.goto(\'/\')'):
                action = line.strip()
                implemented_actions.append(action)
        
        # DO NOT add the current action - we want to capture page state BEFORE executing it
        # The current action is what we're trying to build, not what we're debugging
        # We only want to capture the state after all previous actions are completed
        
        template_path = self.target.get_template_path('debug_spec')
        return self.template_manager.render_template(
            template_path,
            implemented_actions='\n    '.join(implemented_actions)
        )
    
    def capture_page_state(self, debug_spec: str, scenario: 'Scenario') -> str:
        """Capture the current page state using the debug spec."""
        # This would typically run the debug spec and capture the output
        # For now, return a placeholder
        return "Page State: Debug spec generated, page state capture not implemented"


class ReferenceHandler:
    """Handles scenario references and dependency management."""
    
    def __init__(self, filesystem, template_manager):
        self.filesystem = filesystem
        self.template_manager = template_manager
    
    def collect_referenced_scenarios(self, action: str, all_actions: list) -> Dict[str, str]:
        """Collect all referenced scenario code for the current action."""
        referenced_scenarios = {}
        
        # Extract all [INCLUDE_REF:name] from the action
        ref_matches = re.findall(r'\[INCLUDE_REF:([^\]]+)\]', action)
        
        for ref_name in ref_matches:
            ref_spec = self._load_referenced_spec(ref_name)
            if ref_spec:
                referenced_scenarios[ref_name] = ref_spec
        
        return referenced_scenarios
    
    def load_referenced_spec(self, scenario_name: str) -> Optional[str]:
        """Load a referenced scenario spec file."""
        referenced_spec_file = f'.glyph/tests/{scenario_name}.spec.js'
        if not self.filesystem.exists(referenced_spec_file):
            logger.warning(f"Referenced scenario spec not found: {referenced_spec_file}")
            return None
        
        try:
            return self.filesystem.read_text(referenced_spec_file)
        except Exception as e:
            logger.warning(f"Failed to load referenced spec {referenced_spec_file}: {e}")
            return None
    
    def extract_ref_name(self, action: str) -> Optional[str]:
        """Extract reference name from action string."""
        match = re.search(r'\[INCLUDE_REF:([^\]]+)\]', action)
        return match.group(1) if match else None
    
    def build_with_references(self, current_spec: str, action: str, accumulated_refs: Dict[str, str], implemented_actions: List[str], all_actions: list, current_action_index: int, scenario: 'Scenario' = None) -> str:
        """Build spec with accumulated references using LLM."""
        # This would handle building specs with references
        # For now, return the current spec
        return current_spec


class SystemStateManager:
    """Manages system state, glyph.md, and system insights."""
    
    def __init__(self, system_state, llm_provider, template_manager):
        self.system_state = system_state
        self.llm_provider = llm_provider
        self.template_manager = template_manager
    
    def get_system_insights(self, scenario: 'Scenario', action: str) -> str:
        """Get relevant system insights for the current scenario and action."""
        # This would use the system state to get relevant insights
        # For now, return a placeholder
        return "No system insights available"
    
    def update_glyph_md(self, page_dump: str, action: str, scenario: 'Scenario') -> None:
        """Update glyph.md with new page state information."""
        # This would update the system state with new information
        # For now, do nothing
        pass
    
    def update_glyph_md_with_patterns(self, pattern_analysis: dict) -> None:
        """Update glyph.md with pattern analysis for SDK design."""
        try:
            sdk_content = self._generate_sdk_content_from_llm(pattern_analysis)
            
            # Update the system state storage
            if hasattr(self.system_state, 'update_glyph_md'):
                self.system_state.update_glyph_md(sdk_content)
            else:
                # Fallback: write directly to file
                glyph_md_path = '.glyph/glyph.md'
                os.makedirs(os.path.dirname(glyph_md_path), exist_ok=True)
                with open(glyph_md_path, 'w') as f:
                    f.write(sdk_content)
                    
        except Exception as e:
            logger.error(f"Failed to update glyph.md with patterns: {e}")
    
    def _generate_sdk_content_from_llm(self, pattern_analysis: dict) -> str:
        """Generate SDK content based on LLM pattern analysis."""
        
        # Get the LLM's analysis
        llm_analysis = pattern_analysis.get('llm_analysis', 'No analysis available')
        guide_count = pattern_analysis.get('guide_count', 0)
        
        # Use the initial SDK template
        template_path = 'initial_sdk.j2'
        sdk_content = self.template_manager.render_template(
            template_path,
            llm_analysis=llm_analysis,
            guide_count=guide_count
        )
        return sdk_content


class ScenarioBuilder:
    def __init__(self, target, config, filesystem=None, system_state=None, llm_provider=None, template_manager=None):
        self.target = target
        self.config = config
        self.llm_provider = llm_provider
        self.filesystem = filesystem
        self.all_guides = {}
        self.system_state = system_state
        self.template_manager = template_manager
        
        # Initialize specialized services
        self.action_converter = ActionConverter(llm_provider, template_manager, target)
        self.spec_generator = SpecGenerator(template_manager, target, filesystem)
        self.debug_spec_manager = DebugSpecManager(target, template_manager)
        self.reference_handler = ReferenceHandler(filesystem, template_manager)
        self.system_state_manager = SystemStateManager(system_state, llm_provider, template_manager)
    
    
    def _load_all_guides(self):
        """Load all available guides into memory."""
        if self.all_guides:
            return
        
        guides_dir = '.glyph/guides'
        
        if not self.filesystem.exists(guides_dir):
            logger.info("No guides directory found, skipping guide loading")
            return
        
        guide_files = self.filesystem.glob(f"{guides_dir}/*.guide")
        logger.info(f"Loading {len(guide_files)} guides into memory")
        
        for guide_file in guide_files:
            try:
                guide = Guide.from_file(guide_file, self.filesystem)
                self.all_guides[guide.name] = guide
                logger.debug(f"Loaded guide: {guide.name}")
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Failed to load guide {guide_file}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error loading guide {guide_file}: {e}")
                raise GuideError(f"Failed to load guide {guide_file}: {e}") from e
        
        logger.info(f"Successfully loaded {len(self.all_guides)} guides")
    
    def build_scenario(self, scenario: 'Scenario', debug_stop: int = None) -> str:
        logger.info(f"Building scenario: {scenario.name}")
        
        self._load_all_guides()
        
        actions = self._get_actions_from_guide(scenario)
        if not actions:
            logger.info("No guide file found, generating actions using LLM...")
            # Get template manager from target
            template_manager = self.target.template_manager
            actions = scenario.list_actions(self.llm_provider, template_manager)
        
        unique_actions = []
        for action in actions:
            if action.strip().startswith('[ref:') and ']' in action:
                ref_start = action.find('[ref:') + 5
                ref_end = action.find(']')
                scenario_name = action[ref_start:ref_end].strip()
                logger.info(f"Including reference to {scenario_name} - will merge logic")
                unique_actions.append(f"[INCLUDE_REF:{scenario_name}]")
            else:
                unique_actions.append(action)
        
        logger.info(f"Found {len(actions)} total actions, building {len(unique_actions)} unique actions:")
        for i, action in enumerate(unique_actions, 1):
            logger.info(f"  {i}. {action}")
        
        spec_file = f'.glyph/tests/{scenario.name}{self.target.get_spec_extension()}'
        if self.filesystem.exists(spec_file):
            self.filesystem.unlink(spec_file)
            logger.info(f"Deleted existing spec: {spec_file}")
        
        current_spec = self.spec_generator.generate_initial_spec()
        implemented_actions = ["Navigate to the root page"]
        action_functions = []  # Collect individual action functions
        reference_functions = {}  # Collect functions from referenced specs
        
        logger.info(f"Building Playwright test...")
        
        for i, action in enumerate(unique_actions, 1):
            if debug_stop and i == debug_stop:
                logger.info(f"🛑 DEBUG STOP: Stopping at action {i}: {action}")
                logger.info(f"Current spec:\n{current_spec}")
                return current_spec
            
            # Check if this is a reference action
            if '[INCLUDE_REF:' in action:
                # Extract and process the reference
                ref_name = self.reference_handler.extract_ref_name(action)
                if ref_name:
                    logger.info(f"📚 Processing reference: {ref_name}")
                    # Load the referenced spec file
                    ref_spec_file = f'.glyph/tests/{ref_name}.spec.js'
                    if self.filesystem.exists(ref_spec_file):
                        ref_spec_content = self.filesystem.read_text(ref_spec_file)
                        # Extract the exported functions from the referenced spec
                        ref_functions = self._extract_functions_from_spec(ref_spec_content)
                        logger.info(f"📚 Extracted {len(ref_functions)} functions from {ref_name}: {list(ref_functions.keys())}")
                        # Add reference functions to our collection
                        reference_functions.update(ref_functions)
                    else:
                        logger.warning(f"Referenced spec file not found: {ref_spec_file}")
                
                # Skip to next action since this is just a reference
                implemented_actions.append(action)
                continue
            
            # Regular action processing - just get the action function
            action_function = self._build_next_action(current_spec, action, implemented_actions, unique_actions, i-1, scenario)
            if action_function:
                action_functions.append(action_function)
            
            implemented_actions.append(action)
        
        # Build the complete spec with all collected action functions and reference functions
        if action_functions or reference_functions:
            logger.info(f"Building complete spec with {len(action_functions)} action functions and {len(reference_functions)} reference functions")
            current_spec = self.spec_generator.build_complete_spec_from_actions_and_references(action_functions, reference_functions, scenario)
        
        self.spec_generator.save_spec(spec_file, current_spec)
        logger.info(f"✅ Saved spec to: {spec_file}")
        
        # Post-build SDK update stage
        try:
            logger.info("🔄 Updating SDK with new spec patterns...")
            self._update_sdk_after_build(scenario, current_spec)
            logger.info("✅ SDK update completed")
        except Exception as e:
            logger.warning(f"⚠️  SDK update failed: {e}")
            logger.info("Continuing without SDK update...")
        
        return current_spec
    
    def _get_actions_from_guide(self, scenario: 'Scenario') -> Optional[List[str]]:
        """Try to load actions from a pre-processed guide file."""
        guide_file = f'.glyph/guides/{scenario.name}.guide'
        if self.filesystem.exists(guide_file):
            try:
                guide = Guide.from_file(guide_file, self.filesystem)
                logger.info(f"Loaded guide: {guide_file}")
                
                # Return the original actions (don't flatten - we'll handle refs during build)
                return guide.actions
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Failed to load guide {guide_file}: {e}")
                return None
            except Exception as e:
                logger.warning(f"Unexpected error loading guide {guide_file}: {e}")
                raise GuideError(f"Failed to load guide {guide_file}: {e}") from e
        else:
            logger.info(f"No guide file found: {guide_file}")
            return None
    

    
    def _build_next_action(self, current_spec: str, action: str, implemented_actions: List[str], all_actions: list, current_action_index: int, scenario: 'Scenario' = None) -> str:
        # Check if this action contains references
        if '[INCLUDE_REF:' in action:
            # Extract the reference name
            ref_name = self.reference_handler.extract_ref_name(action)
            if ref_name:
                logger.info(f"Processing reference: {ref_name}")
                # Load the referenced spec file
                ref_spec_file = f'.glyph/tests/{ref_name}.spec.js'
                if self.filesystem.exists(ref_spec_file):
                    ref_spec_content = self.filesystem.read_text(ref_spec_file)
                    # Extract the exported functions from the referenced spec
                    ref_functions = self._extract_functions_from_spec(ref_spec_content)
                    logger.info(f"Extracted {len(ref_functions)} functions from {ref_name}: {list(ref_functions.keys())}")
                    # Return the reference functions to be included in the final spec
                    return ref_functions
                else:
                    logger.warning(f"Referenced spec file not found: {ref_spec_file}")
            return None
        
        # Regular action - proceed with normal build process
        debug_spec = self.debug_spec_manager.generate_debug_spec(current_spec, action)
        page_dump = self.debug_spec_manager.capture_page_state(debug_spec, scenario)
        
        # Update glyph.md with intelligent analysis (only if we have valid page state)
        if page_dump and "Page State:" in page_dump:
            self.system_state_manager.update_glyph_md(page_dump, action, scenario)
        
        # Get system insights from glyph.md (this is our primary source of truth)
        system_insights = self.system_state_manager.get_system_insights(scenario, action)
        
        # Use LLM-driven action conversion for better context understanding
        try:
            logger.info(f"Attempting LLM action conversion for: {action}")
            logger.info(f"DEBUG: current_spec length: {len(current_spec)}")
            logger.info(f"DEBUG: implemented_actions: {implemented_actions}")
            logger.info(f"DEBUG: action: {action}")
            logger.info(f"DEBUG: scenario.name: {scenario.name}")
            
            # Convert the action to Playwright code using LLM with full context
            playwright_code = self.action_converter.convert_action_to_playwright(
                action, 
                implemented_actions, 
                system_insights,
                page_dump
            )
            
            if playwright_code:
                logger.info(f"LLM conversion succeeded, generated: {playwright_code}")
                # Just return the action function, don't build the complete spec yet
                action_name = self.spec_generator._generate_action_function_name(action)
                action_function = f'''async function {action_name}(page) {{
    {playwright_code}
}}'''
                logger.info(f"DEBUG: Created action function: {action_name}")
                return action_function
            else:
                logger.info("LLM conversion returned None, falling back to template approach")
        except Exception as e:
            logger.warning(f"LLM action conversion failed, falling back to template approach: {e}")
        
        # Fallback to template approach
        logger.info("Using template approach for action conversion")
        # For now, return None since we don't have the template approach implemented
        return None
    
    def _extract_functions_from_spec(self, spec_content: str) -> dict:
        """Extract function definitions and their names from a spec file."""
        functions = {}
        lines = spec_content.split('\n')
        current_function = []
        in_function = False
        function_name = None
        
        for line in lines:
            if line.strip().startswith('async function ') or line.strip().startswith('function '):
                if current_function and function_name:
                    functions[function_name] = '\n'.join(current_function)
                current_function = [line]
                in_function = True
                # Extract function name
                if 'async function ' in line:
                    function_name = line.split('async function ')[1].split('(')[0].strip()
                else:
                    function_name = line.split('function ')[1].split('(')[0].strip()
            elif in_function and line.strip() == '}':
                current_function.append(line)
                in_function = False
                if function_name:
                    functions[function_name] = '\n'.join(current_function)
                current_function = []
                function_name = None
            elif in_function:
                current_function.append(line)
        
        # Don't forget the last function
        if current_function and function_name:
            functions[function_name] = '\n'.join(current_function)
        
        return functions
    

    
    def _update_spec_with_action(self, iteration_prompt: str, action: str, all_actions: list, current_action_index: int) -> str:
        # Highlight the current action in the full action list
        highlighted_actions = []
        for i, act in enumerate(all_actions):
            if i == current_action_index:
                highlighted_actions.append(f"**CURRENT ACTION: {act}**")
            else:
                highlighted_actions.append(f"- {act}")
        
        action_context = "\n".join(highlighted_actions)
        
        return self.llm_provider.generate(iteration_prompt, action_context)

    
    def _update_sdk_after_build(self, scenario: 'Scenario', spec_content: str):
        """Update the SDK after building a new spec to incorporate new patterns."""
        try:
            # Get current SDK content
            current_sdk = self._get_current_sdk_content()
            
            # Get SDK design guidelines from glyph.md
            sdk_design = self._get_sdk_design_guidelines()
            
            # Use LLM to analyze and update the SDK
            updated_sdk = self._analyze_and_update_sdk(
                current_sdk, 
                scenario.name, 
                spec_content, 
                sdk_design
            )
            
            # Save the updated SDK
            if updated_sdk:
                self._save_updated_sdk(updated_sdk)
                logger.info(f"✅ SDK updated with patterns from {scenario.name}")
            
        except Exception as e:
            logger.error(f"Failed to update SDK: {e}")
            raise
    
    def _get_current_sdk_content(self) -> str:
        """Get the current SDK content from sdk.js if it exists."""
        sdk_file = '.glyph/sdk.js'
        if self.filesystem.exists(sdk_file):
            return self.filesystem.read_text(sdk_file)
        return "// No existing SDK found"
    
    def _get_sdk_design_guidelines(self) -> str:
        """Get SDK design guidelines from glyph.md."""
        glyph_md_file = '.glyph/glyph.md'
        if self.filesystem.exists(glyph_md_file):
            return self.filesystem.read_text(glyph_md_file)
        return "// No SDK design guidelines found"
    
    def _analyze_and_update_sdk(self, current_sdk: str, scenario_name: str, spec_content: str, sdk_design: str) -> str:
        """Use LLM to analyze the new spec and update the SDK."""
        # Use the SDK updater template
        template_path = 'sdk_updater.j2'
        prompt = self.template_manager.render_template(
            template_path,
            current_sdk=current_sdk,
            scenario_name=scenario_name,
            spec_content=spec_content,
            sdk_design=sdk_design
        )
        
        # Get LLM analysis and update
        response = self.llm_provider.generate(prompt, "sdk_update")
        
        # Extract the updated SDK content from the response
        # The LLM should return the complete updated SDK
        return response
    
    def _save_updated_sdk(self, updated_sdk: str):
        """Save the updated SDK to sdk.js."""
        sdk_file = '.glyph/sdk.js'
        try:
            self.filesystem.write_text(sdk_file, updated_sdk)
            logger.info(f"✅ Updated SDK saved to {sdk_file}")
        except Exception as e:
            logger.error(f"Failed to save updated SDK: {e}")
            raise
    
    def _save_spec(self, spec_file: str, spec_content: str):
        """Save the final spec to file."""
        self.filesystem.write_text(spec_file, spec_content)
