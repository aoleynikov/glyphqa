from typing import List, Optional, TYPE_CHECKING, Dict
from pathlib import Path
import logging
import base64

if TYPE_CHECKING:
    from .models import Scenario, Guide
    from .system_catalog import SystemCatalog

logger = logging.getLogger(__name__)


class ScenarioBuilder:
    def __init__(self, target, config):
        self.target = target
        self.config = config
        self.llm_provider = config.llm
        self.filesystem = None  # Will be initialized when needed
        self.all_guides = {}  # Cache for all loaded guides
        self.system_catalog = None  # Will be initialized when needed
    
    def _get_filesystem(self):
        """Get filesystem instance, creating it if needed."""
        if self.filesystem is None:
            from .filesystem import FileSystem
            self.filesystem = FileSystem()
        return self.filesystem
    
    def _get_system_catalog(self):
        """Get system catalog instance, creating it if needed."""
        if self.system_catalog is None:
            from .system_catalog import SystemCatalog
            filesystem = self._get_filesystem()
            self.system_catalog = SystemCatalog(filesystem)
        return self.system_catalog
    
    def _load_all_guides(self):
        """Load all available guides into memory."""
        if self.all_guides:  # Already loaded
            return
        
        filesystem = self._get_filesystem()
        guides_dir = '.glyph/guides'
        
        if not filesystem.exists(guides_dir):
            logger.info("No guides directory found, skipping guide loading")
            return
        
        guide_files = filesystem.glob(f"{guides_dir}/*.guide")
        logger.info(f"Loading {len(guide_files)} guides into memory")
        
        for guide_file in guide_files:
            try:
                from .models import Guide
                guide = Guide.from_file(guide_file, filesystem)
                self.all_guides[guide.name] = guide
                logger.debug(f"Loaded guide: {guide.name}")
            except Exception as e:
                logger.warning(f"Failed to load guide {guide_file}: {e}")
        
        logger.info(f"Successfully loaded {len(self.all_guides)} guides")
    
    def build_scenario(self, scenario: 'Scenario', debug_stop: int = None) -> str:
        logger.info(f"Building scenario: {scenario.name}")
        
        # Load all guides into memory
        self._load_all_guides()
        
        # Try to load pre-processed actions from guide file
        actions = self._get_actions_from_guide(scenario)
        if not actions:
            # Fallback to generating actions using LLM
            logger.info("No guide file found, generating actions using LLM...")
            actions = scenario.list_actions(self.llm_provider)
        
        # Handle reference actions by including referenced logic
        unique_actions = []
        for action in actions:
            if action.strip().startswith('[ref:') and ']' in action:
                # Extract scenario name for logging
                ref_start = action.find('[ref:') + 5
                ref_end = action.find(']')
                scenario_name = action[ref_start:ref_end].strip()
                logger.info(f"Including reference to {scenario_name} - will merge logic")
                # Add a special marker to include referenced logic
                unique_actions.append(f"[INCLUDE_REF:{scenario_name}]")
            else:
                unique_actions.append(action)
        
        logger.info(f"Found {len(actions)} total actions, building {len(unique_actions)} unique actions:")
        for i, action in enumerate(unique_actions, 1):
            logger.info(f"  {i}. {action}")
        
        spec_file = f'.glyph/tests/{scenario.name}.spec.js'
        if self.filesystem.exists(spec_file):
            self.filesystem.unlink(spec_file)
            logger.info(f"Deleted existing spec: {spec_file}")
        
        current_spec = self._generate_initial_spec()
        implemented_actions = ["Navigate to the root page"]
        
        logger.info(f"Building Playwright test...")
        
        for i, action in enumerate(unique_actions, 1):
            if debug_stop and i == debug_stop:
                logger.info(f"🛑 DEBUG STOP: Stopping at action {i}: {action}")
                logger.info(f"Current spec:\n{current_spec}")
                return current_spec
            
            current_spec = self._build_next_action(current_spec, action, implemented_actions, unique_actions, i-1)
            implemented_actions.append(action)
        
        self._save_spec(spec_file, current_spec)
        logger.info(f"✅ Saved spec to: {spec_file}")
        
        return current_spec
    
    def _get_actions_from_guide(self, scenario: 'Scenario') -> Optional[List[str]]:
        """Try to load actions from a pre-processed guide file."""
        filesystem = self._get_filesystem()
        guide_file = f'.glyph/guides/{scenario.name}.guide'
        if filesystem.exists(guide_file):
            try:
                from .models import Guide
                guide = Guide.from_file(guide_file, filesystem)
                logger.info(f"Loaded guide: {guide_file}")
                
                # Return the original actions (don't flatten - we'll handle refs during build)
                return guide.actions
            except Exception as e:
                logger.warning(f"Failed to load guide {guide_file}: {e}")
                return None
        else:
            logger.info(f"No guide file found: {guide_file}")
            return None
    
    def _generate_initial_spec(self) -> str:
        initial_system_prompt = self.target.template_manager.get_playwright_template('initial_spec')
        user_prompt = "Navigate to the root page"
        return self.llm_provider.generate(initial_system_prompt, user_prompt)
    
    def _build_next_action(self, current_spec: str, action: str, implemented_actions: List[str], all_actions: list, current_action_index: int) -> str:
        # Check if this is a reference inclusion marker
        if action.strip().startswith('[INCLUDE_REF:') and ']' in action:
            # Extract scenario name from reference
            ref_start = action.find('[INCLUDE_REF:') + 13
            ref_end = action.find(']')
            scenario_name = action[ref_start:ref_end].strip()
            
            # Include the referenced scenario logic
            return self._include_referenced_spec(current_spec, scenario_name)
        
        # Regular action - proceed with normal build process
        debug_spec = self._generate_debug_spec(current_spec)
        page_dump = self._capture_page_state(debug_spec)
        
        # Update glyph.md with intelligent analysis (only if we have valid page state)
        if page_dump and "Page State:" in page_dump:
            self._update_glyph_md(page_dump, action)
        
        # Get system insights from glyph.md (this is our primary source of truth)
        system_insights = self._get_system_insights()
        iteration_prompt = self._generate_iteration_prompt(current_spec, implemented_actions, system_insights)
        return self._update_spec_with_action(iteration_prompt, action, all_actions, current_action_index)
    
    def _generate_debug_spec(self, current_spec: str) -> str:
        # Extract the implemented actions from the current spec
        # Parse the current spec to extract the action lines
        lines = current_spec.split('\n')
        implemented_actions = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('await page.') and not line.startswith('await page.goto(\'/\')'):
                # Keep the await and semicolon for proper Playwright syntax
                action = line.strip()
                implemented_actions.append(action)
        
        # Use the template to generate debug spec
        return self.target.template_manager.get_playwright_template(
            'debug_spec',
            implemented_actions='\n    '.join(implemented_actions)
        )
    
    def _capture_page_state(self, debug_spec: str) -> str:
        """Capture the current page state by running a debug spec."""
        try:
            return self.target.run_debug_spec(debug_spec)
        except Exception as e:
            logger.warning(f"Debug spec execution failed: {e}")
            # Return a minimal page state if debug spec fails
            return """Current URL: http://localhost:3000/
Page Title: React App
Page State: {
  "url": "http://localhost:3000/",
  "title": "React App",
  "elements": [],
  "visibleElements": [],
  "navigationElements": [],
  "formElements": [],
  "forms": [],
  "interactionReport": {
    "buttons": [],
    "inputs": [],
    "selects": [],
    "links": [],
    "labels": []
  },
  "elementCounts": {
    "total": 0,
    "visible": 0,
    "forms": 0,
    "inputs": 0,
    "buttons": 0,
    "selects": 0,
    "links": 0,
    "labels": 0
  }
}"""
    
    def _update_glyph_md(self, page_dump: str, action: str):
        """Update glyph.md with intelligent analysis of the page state."""
        try:
            from .glyph_md_updater import GlyphMdUpdater
            from pathlib import Path
            
            # Create GlyphMdUpdater instance
            glyph_dir = Path('.glyph')
            updater = GlyphMdUpdater(glyph_dir, self.llm_provider)
            
            # Update glyph.md with the debug output
            # We need to pass the scenario name, but we don't have it in this context
            # For now, use a generic name
            scenario_name = "current_scenario"
            
            updated = updater.update_from_debug_spec(scenario_name, action, page_dump)
            if updated:
                logger.info("Updated glyph.md with new insights")
            else:
                logger.debug("No updates needed for glyph.md")
                
        except Exception as e:
            logger.warning(f"Failed to update glyph.md for action '{action}': {e}")
            # Fall back to the old system catalog method for now
            self._catalog_page_state_fallback(page_dump, action)
    
    def _catalog_page_state_fallback(self, page_dump: str, action: str):
        """Fallback to old system catalog method if GlyphMdUpdater fails."""
        try:
            # Extract the JSON part from the page dump
            # Look for "Page State:" followed by JSON
            page_state_marker = "Page State:"
            json_start = page_dump.find(page_state_marker)
            if json_start == -1:
                # Fallback: look for just the opening brace
                json_start = page_dump.find('{')
                if json_start == -1:
                    logger.debug(f"No JSON found in page dump for action: {action}")
                    return
            else:
                # Skip past "Page State:" to find the actual JSON start
                json_start = page_dump.find('{', json_start)
                if json_start == -1:
                    logger.debug(f"No JSON start found after 'Page State:' for action: {action}")
                    return
            
            # Find the end of the JSON object
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(page_dump[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            import json
            json_str = page_dump[json_start:json_end]
            
            # Debug: Log the JSON string being parsed
            logger.debug(f"Parsing JSON for action '{action}': {json_str[:200]}...")
            
            # Clean up the JSON string - remove leading/trailing whitespace
            json_str = json_str.strip()
            
            # Parse the JSON
            try:
                page_data = json.loads(json_str)
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON decode error for action '{action}': {json_error}")
                logger.debug(f"JSON string: {json_str[:500]}...")
                
                # Try multiple cleanup strategies
                cleanup_strategies = [
                    # Strategy 1: Basic whitespace normalization
                    lambda s: s.replace('\n', ' ').replace('\r', ' ').strip(),
                    # Strategy 2: Remove all extra whitespace
                    lambda s: ' '.join(s.split()),
                    # Strategy 3: Try to find JSON object boundaries
                    lambda s: s[s.find('{'):s.rfind('}')+1] if '{' in s and '}' in s else s,
                    # Strategy 4: Remove any non-JSON content before/after
                    lambda s: s[s.find('{'):] if '{' in s else s
                ]
                
                for i, strategy in enumerate(cleanup_strategies):
                    try:
                        cleaned_json = strategy(json_str)
                        if cleaned_json and cleaned_json != json_str:
                            logger.debug(f"Trying cleanup strategy {i+1}")
                            page_data = json.loads(cleaned_json)
                            logger.info(f"Successfully parsed JSON using cleanup strategy {i+1}")
                            break
                    except json.JSONDecodeError:
                        continue
                else:
                    logger.error(f"Failed to parse JSON even after all cleanup strategies for action '{action}'")
                    logger.debug(f"Final JSON string: {json_str[:500]}...")
                    return
            
            system_catalog = self._get_system_catalog()
            system_catalog.catalog_page_state(
                url=page_data.get('url', ''),
                page_data=page_data,
                action_context=action
            )
        except Exception as e:
            logger.warning(f"Failed to catalog page state for action '{action}': {e}")
            # Log the first 500 characters of the page dump for debugging
            logger.debug(f"Page dump preview: {page_dump[:500]}...")
    
    def _get_system_insights(self) -> str:
        """Get the full glyph.md content as system knowledge for the prompt."""
        try:
            glyph_md_path = '.glyph/glyph.md'
            if self.filesystem.exists(glyph_md_path):
                glyph_content = self.filesystem.read_text(glyph_md_path)
                return glyph_content
            else:
                return "No system knowledge available yet. glyph.md not found."
        except Exception as e:
            logger.warning(f"Failed to read glyph.md: {e}")
            return "System knowledge unavailable."
    
    def _generate_page_summary(self, page_dump: str) -> str:
        """Generate a concise summary of the page state for the LLM."""
        try:
            # Extract the JSON part from the page dump
            # Look for "Page State:" followed by JSON
            page_state_marker = "Page State:"
            json_start = page_dump.find(page_state_marker)
            if json_start == -1:
                # Fallback: look for just the opening brace
                json_start = page_dump.find('{')
                if json_start == -1:
                    return "Page state data not available"
            else:
                # Skip past "Page State:" to find the actual JSON start
                json_start = page_dump.find('{', json_start)
                if json_start == -1:
                    return "Page state data not available"
            
            # Find the end of the JSON object
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(page_dump[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            import json
            json_str = page_dump[json_start:json_end]
            page_data = json.loads(json_str)
            
            summary_parts = []
            
            # Current page info
            summary_parts.append(f"Current URL: {page_data.get('url', 'unknown')}")
            summary_parts.append(f"Page Title: {page_data.get('title', 'unknown')}")
            
            # Form elements
            form_elements = page_data.get('formElements', [])
            if form_elements:
                input_types = [el.get('type', 'unknown') for el in form_elements if el.get('tag') == 'input']
                button_texts = [el.get('textContent', 'unknown') for el in form_elements if el.get('tag') == 'button']
                summary_parts.append(f"Form elements: {len(form_elements)} total")
                if input_types:
                    summary_parts.append(f"Input fields: {', '.join(input_types)}")
                if button_texts:
                    summary_parts.append(f"Buttons: {', '.join(button_texts)}")
            
            # Navigation elements
            nav_elements = page_data.get('navigationElements', [])
            if nav_elements:
                nav_texts = [el.get('textContent', 'unknown') for el in nav_elements if el.get('textContent')]
                summary_parts.append(f"Navigation: {', '.join(nav_texts)}")
            
            # Element counts
            counts = page_data.get('elementCounts', {})
            if counts:
                summary_parts.append(f"Visible elements: {counts.get('visible', 0)}/{counts.get('total', 0)}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            return f"Error parsing page state: {e}"
    
    def _generate_iteration_prompt(self, current_spec: str, implemented_actions: List[str], system_insights: str) -> str:
        actions_list = "\n".join(f"- {action}" for action in implemented_actions)
        return self.target.template_manager.get_playwright_template(
            'iteration_spec',
            action_count=len(implemented_actions),
            actions_list=actions_list,
            current_spec=current_spec,
            system_insights=system_insights
        )
    
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
    

    

    
    def _include_referenced_spec(self, current_spec: str, scenario_name: str) -> str:
        """Add an import and function call for the referenced scenario."""
        # Check if the referenced scenario spec exists
        referenced_spec_file = f'.glyph/tests/{scenario_name}.spec.js'
        if not self.filesystem.exists(referenced_spec_file):
            logger.warning(f"Referenced scenario spec not found: {referenced_spec_file}")
            return current_spec
        
        # Read the referenced spec to extract the function name
        referenced_spec = self.filesystem.read_text(referenced_spec_file)
        
        # Extract the test function name from the referenced spec
        import re
        test_match = re.search(r'test\([\'"]([^\'"]+)[\'"]', referenced_spec)
        if not test_match:
            logger.warning(f"Could not extract test function name from {referenced_spec_file}")
            return current_spec
        
        test_function_name = test_match.group(1)
        
        # Create a helper function name for the referenced scenario
        helper_function_name = f"perform_{scenario_name.replace('-', '_')}"
        
        # Add the import at the top of the file
        import_statement = f"import {{ {helper_function_name} }} from './{scenario_name}.spec.js';"
        
        # Find where to insert the import (after the existing imports)
        if 'import { test, expect }' in current_spec:
            # Insert after the existing import
            import_end = current_spec.find('\n', current_spec.find('import { test, expect }'))
            if import_end == -1:
                import_end = len(current_spec)
            
            new_spec = (
                current_spec[:import_end] + '\n' + import_statement + '\n' +
                current_spec[import_end:]
            )
        else:
            # No existing imports, add at the beginning
            new_spec = import_statement + '\n\n' + current_spec
        
        # Add the function call in the test
        function_call = f"    await {helper_function_name}(page);"
        
        # Find where to insert the function call (after page.goto if it exists, otherwise at the beginning of the test)
        if 'await page.goto' in new_spec:
            # Insert after the page.goto line
            goto_end = new_spec.find('\n', new_spec.rfind('await page.goto'))
            if goto_end == -1:
                goto_end = len(new_spec)
            
            new_spec = (
                new_spec[:goto_end] + '\n' + function_call + '\n' +
                new_spec[goto_end:]
            )
        else:
            # No page.goto, insert at the beginning of the test function
            test_start = new_spec.find('async ({ page }) => {')
            if test_start != -1:
                test_body_start = new_spec.find('{', test_start) + 1
                new_spec = (
                    new_spec[:test_body_start] + '\n' + function_call + '\n' +
                    new_spec[test_body_start:]
                )
        
        return new_spec
    
    def _save_spec(self, spec_file: str, spec_content: str):
        """Save the final spec to file."""
        self.filesystem.write_text(spec_file, spec_content)
