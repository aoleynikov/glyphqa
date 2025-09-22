"""
System Analysis Agent

Handles system exploration, page state capture, and knowledge management.
This agent is responsible for "looking around" the system to understand
its actual structure and behavior.
"""

import json
import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .llm import LLMProvider
from .templates import TemplateManager
from .filesystem import FileSystem

logger = logging.getLogger(__name__)


@dataclass
class PageElement:
    """Represents a page element found during analysis."""
    tag: str
    text_content: Optional[str] = None
    class_name: Optional[str] = None
    element_id: Optional[str] = None
    element_type: Optional[str] = None
    selector: Optional[str] = None


@dataclass
class PageState:
    """Represents the current state of a page."""
    url: str
    title: str
    timestamp: str
    elements: List[PageElement]
    context: str = ""


class SystemAnalysisAgent:
    """
    Agent responsible for system analysis, page state capture, and knowledge management.
    
    This agent:
    1. Executes debug specs to capture page state
    2. Analyzes page elements and structure
    3. Manages system knowledge in glyph.md
    4. Provides application-specific context and guidance
    4. Provides selector resolution based on actual system behavior
    """
    
    def __init__(self, llm_provider: LLMProvider, template_manager: TemplateManager, filesystem: FileSystem, config=None):
        self.llm_provider = llm_provider
        self.template_manager = template_manager
        self.filesystem = filesystem
        self.config = config
        self.debug_spec_file = Path('.glyph/tests/debug_system.spec.js')
        self.glyph_md_file = Path('.glyph/glyph.md')
        
        # Initialize system knowledge
        self._ensure_debug_spec_exists()
        self._load_system_knowledge()
        self.application_context = self._get_application_context()
        
        # Initialize iterative build state
        self.accumulated_steps = []  # List of all previous steps executed
        self.current_scenario = None
    
    def start_scenario(self, scenario_name: str):
        """Start a new scenario, resetting accumulated steps."""
        self.current_scenario = scenario_name
        self.accumulated_steps = []
        logger.info(f"Started iterative build for scenario: {scenario_name}")
    
    def add_step(self, step_description: str, js_code: str):
        """Add a step to the accumulated steps list."""
        self.accumulated_steps.append({
            'description': step_description,
            'js_code': js_code
        })
        logger.info(f"Added step to accumulated steps: {step_description}")
    
    
    
    def _ensure_debug_spec_exists(self):
        """Ensure the debug spec file exists and is properly configured."""
        if not self.debug_spec_file.exists():
            self._create_debug_spec()
    
    def _create_debug_spec(self):
        """Create the reusable debug spec file."""
        base_url = self.config.connection.url
        debug_spec_content = self.template_manager.render_template(
            'agent/system_debug_spec.j2',
            base_url=base_url
        )
        self.filesystem.write_text(self.debug_spec_file, debug_spec_content)
    
    def _load_system_knowledge(self):
        """Load existing system knowledge from glyph.md."""
        if self.glyph_md_file.exists():
            content = self.filesystem.read_text(self.glyph_md_file)
            self.system_knowledge = self._parse_glyph_md(content)
        else:
            self.system_knowledge = {}
    
    def _get_application_context(self) -> Dict[str, Any]:
        """Get generic application context without hardcoded selectors."""
        return {
            'application_type': 'Web application',
            'base_url': self.config.connection.url,
            'important_notes': [
                'Use waitForTimeout() for UI transitions',
                'Use unique identifiers (Date.now()) to avoid conflicts in tests',
                'Form fields may exist in modals or on main pages',
                'Check actual page structure for correct selectors',
                'Verify redirect behavior for navigation functionality',
                'Use only selectors that exist in the actual page structure'
            ]
        }
    
    def _parse_glyph_md(self, content: str) -> Dict[str, Any]:
        """Parse glyph.md content into structured knowledge."""
        # Simple parsing - could be enhanced with more sophisticated parsing
        knowledge = {
            'pages': {},
            'elements': {},
            'selectors': {},
            'patterns': {}
        }
        
        # Extract page information
        page_sections = re.findall(r'## Page: (.+?)\n(.*?)(?=## |$)', content, re.DOTALL)
        for page_name, page_content in page_sections:
            knowledge['pages'][page_name] = {
                'content': page_content.strip(),
                'elements': self._extract_elements_from_content(page_content)
            }
        
        return knowledge
    
    def _extract_elements_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract element information from markdown content."""
        elements = []
        # Look for element descriptions in the content
        element_patterns = re.findall(r'- (.+?): (.+)', content)
        for element_desc, selector in element_patterns:
            elements.append({
                'description': element_desc,
                'selector': selector
            })
        return elements
    
    def capture_page_state(self, step_description: str, context: str = "") -> PageState:
        """
        Capture the current page state after executing all accumulated steps.
        
        Args:
            step_description: Description of the current step (for context)
            context: Context description for this capture
            
        Returns:
            PageState object with captured information
        """
        try:
            # Skip if step description is empty or invalid
            if not step_description or step_description.strip() == '' or step_description == '[]':
                print(f"DEBUG: Skipping capture_page_state with empty step description: '{step_description}'")
                return PageState(
                    url="unknown",
                    title="unknown",
                    timestamp="",
                    elements=[],
                    context="Skipped: Empty step description"
                )
            
            # Update debug spec with all accumulated steps
            self._update_debug_spec_with_accumulated_steps(step_description)
            
            # Execute the debug spec
            result = self._execute_debug_spec()
            
            # Parse the results
            page_state = self._parse_debug_output(result, context)
            
            # Store the captured page state for use in context
            self.last_captured_page_state = page_state
            from .build_output_manager import build_output
            build_output.page_state_capture(len(page_state.elements))
            
            # Update system knowledge
            self._update_system_knowledge(page_state)
            
            
            return page_state
            
        except Exception as e:
            print(f"Failed to capture page state: {e}")
            return PageState(
                url="unknown",
                title="unknown", 
                timestamp="",
                elements=[],
                context=f"Error: {str(e)}"
            )
    
    def _update_debug_spec(self, step_description: str):
        """Update the debug spec with the given step description."""
        base_url = self.config.connection.url
        debug_spec_content = self.template_manager.render_template(
            'agent/system_debug_spec.j2',
            step_description=step_description,
            base_url=base_url
        )
        self.filesystem.write_text(self.debug_spec_file, debug_spec_content)
    
    def _update_debug_spec_with_accumulated_steps(self, current_step_description: str):
        """Update the debug spec with all accumulated steps."""
        # Get base URL from config
        base_url = self.config.connection.url
        
        # Debug: Print what we're receiving
        from .build_output_manager import build_output
        build_output.debug_info(f"Processing step: {current_step_description}")
        
        # Pass accumulated steps to template without hardcoding any application behavior
        existing_specs = []
        if self.accumulated_steps:
            # Use accumulated steps as-is without generating hardcoded JavaScript
            existing_specs = [{
                'name': 'Accumulated Steps',
                'steps': self.accumulated_steps
            }]
        
        # Check if we have SDK functions available
        sdk_functions = self._get_available_sdk_functions()
        
        debug_spec_content = self.template_manager.render_template(
            'agent/system_debug_spec.j2',
            accumulated_steps=self.accumulated_steps,
            current_step_description=current_step_description,
            base_url=base_url,
            existing_specs=existing_specs,
            sdk_functions=sdk_functions
        )
        self.filesystem.write_text(self.debug_spec_file, debug_spec_content)
    
    def _get_available_sdk_functions(self) -> List[str]:
        """Get list of available SDK functions."""
        try:
            sdk_file = Path('.glyph/sdk.js')
            if sdk_file.exists():
                sdk_content = sdk_file.read_text()
                # Extract function names from SDK
                import re
                function_pattern = r'async function (\w+)\('
                functions = re.findall(function_pattern, sdk_content)
                return functions
            return []
        except Exception as e:
            print(f"DEBUG: Failed to read SDK functions: {e}")
            return []
    
    def _execute_debug_spec(self) -> Dict[str, Any]:
        """Execute the debug spec and return the results."""
        try:
            result = subprocess.run(
                ['npx', 'playwright', 'test', 'tests/debug_system.spec.js', '--timeout=10000'],
                cwd='.glyph',
                capture_output=True,
                text=True,
                timeout=20  # Increased timeout
            )
            
            # Check if execution was successful
            if result.returncode == 0:
                return {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': True
                }
            else:
                # Debug spec failed, but we can still try to extract some page state
                from .build_output_manager import build_output
                build_output.debug_info(f"Debug spec failed (code: {result.returncode})")
                return {
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': False
                }
            
        except subprocess.TimeoutExpired:
            from .build_output_manager import build_output
            build_output.debug_info("Debug spec execution timed out")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Debug spec execution timed out',
                'success': False
            }
        except Exception as e:
            from .build_output_manager import build_output
            build_output.debug_info(f"Debug spec execution failed: {e}")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def _parse_debug_output(self, result: Dict[str, Any], context: str) -> PageState:
        """Parse the debug spec output into a PageState object."""
        output = result['stdout'] + result['stderr']
        
        # Look for "Page State:" in the output
        if "Page State:" in output:
            try:
                json_match = re.search(r'Page State:\s*(\{.*\})', output, re.DOTALL)
                if json_match:
                    page_data = json.loads(json_match.group(1))
                    
                    # Convert to PageState object
                    elements = []
                    for element_data in page_data.get('elements', []):
                        element = PageElement(
                            tag=element_data.get('tag', ''),
                            text_content=element_data.get('textContent'),
                            class_name=element_data.get('className'),
                            element_id=element_data.get('id'),
                            element_type=element_data.get('type')
                        )
                        element.selector = self._generate_selector(element)
                        elements.append(element)
                    
                    return PageState(
                        url=page_data.get('url', ''),
                        title=page_data.get('title', ''),
                        timestamp=page_data.get('timestamp', ''),
                        elements=elements,
                        context=context
                    )
            except Exception as e:
                print(f"Failed to parse page state JSON: {e}")
        
        # Fallback: return empty state with better error info
        error_msg = result.get('stderr', 'Unknown error')
        from .build_output_manager import build_output
        build_output.debug_info(f"Failed to parse page state: {error_msg}")
        return PageState(
            url="unknown",
            title="unknown",
            timestamp="",
            elements=[],
            context=f"Failed to capture: {error_msg}"
        )
    
    def _generate_selector(self, element: PageElement) -> str:
        """Generate a Playwright selector for the given element."""
        # Prefer ID if available
        if element.element_id:
            return f'#{element.element_id}'
        
        # Use text content with appropriate tag
        if element.text_content:
            return f'{element.tag}:has-text(\'{element.text_content}\')'
        
        # Fallback to class
        if element.class_name:
            first_class = element.class_name.split()[0]
            return f'.{first_class}'
        
        return element.tag
    
    def _update_system_knowledge(self, page_state: PageState):
        """Update system knowledge with new page state information."""
        # Update glyph.md with new information
        self._update_glyph_md(page_state)
        
        # Update in-memory knowledge
        page_key = page_state.url or page_state.title
        if page_key not in self.system_knowledge.get('pages', {}):
            self.system_knowledge.setdefault('pages', {})[page_key] = {
                'content': '',
                'elements': []
            }
        
        # Add new elements
        for element in page_state.elements:
            if element.text_content:
                element_info = {
                    'description': f"{element.tag} with text '{element.text_content}'",
                    'selector': element.selector or f"{element.tag}:has-text('{element.text_content}')"
                }
                self.system_knowledge['pages'][page_key]['elements'].append(element_info)
    
    def _update_glyph_md(self, page_state: PageState):
        """Update glyph.md file with new system knowledge."""
        try:
            # Read existing content
            if self.glyph_md_file.exists():
                existing_content = self.filesystem.read_text(self.glyph_md_file)
            else:
                existing_content = "# System Knowledge\n\n"
            
            # Add new page information
            page_key = page_state.url or page_state.title
            timestamp = page_state.timestamp
            
            new_content = f"\n## Page: {page_key}\n"
            new_content += f"**Captured:** {timestamp}\n"
            new_content += f"**URL:** {page_state.url}\n"
            new_content += f"**Title:** {page_state.title}\n\n"
            
            if page_state.elements:
                new_content += "**Elements Found:**\n"
                for element in page_state.elements:
                    if element.text_content:
                        new_content += f"- {element.tag} '{element.text_content}': {element.selector}\n"
            
            new_content += "\n"
            
            # Append to existing content
            updated_content = existing_content + new_content
            self.filesystem.write_text(self.glyph_md_file, updated_content)
            
        except Exception as e:
            print(f"Failed to update glyph.md: {e}")
    
    def resolve_selector(self, description: str, context: str = "") -> Optional[str]:
        """
        Resolve a selector based on element description and system knowledge.
        
        Args:
            description: Description of the element to find
            context: Additional context about where to look
            
        Returns:
            Resolved selector or None if not found
        """
        # Search through system knowledge for matching elements
        for page_name, page_info in self.system_knowledge.get('pages', {}).items():
            for element in page_info.get('elements', []):
                if self._matches_description(description, element['description']):
                    return element['selector']
        
        return None
    
    def _matches_description(self, description: str, element_desc: str) -> bool:
        """Check if a description matches an element description."""
        description_lower = description.lower()
        element_desc_lower = element_desc.lower()
        
        # Simple matching - could be enhanced with LLM-based matching
        key_terms = description_lower.split()
        return any(term in element_desc_lower for term in key_terms if len(term) > 2)
    
    def get_system_summary(self) -> str:
        """Get a summary of current system knowledge."""
        if not self.system_knowledge.get('pages'):
            return "No system knowledge available yet."
        
        summary = f"System Knowledge Summary:\n"
        summary += f"Pages analyzed: {len(self.system_knowledge['pages'])}\n"
        
        total_elements = sum(
            len(page_info.get('elements', [])) 
            for page_info in self.system_knowledge['pages'].values()
        )
        summary += f"Total elements found: {total_elements}\n"
        
        return summary
    
    def analyze_page_for_selectors(self, js_actions: List[str], target_descriptions: List[str]) -> Dict[str, str]:
        """
        Analyze a page to find selectors for specific target descriptions.
        
        Args:
            js_actions: Actions to execute to reach the page
            target_descriptions: List of element descriptions to find
            
        Returns:
            Dictionary mapping descriptions to resolved selectors
        """
        resolved_selectors = {}
        for description in target_descriptions:
            selector = self.resolve_selector(description)
            if selector:
                resolved_selectors[description] = selector
            else:
                # Capture page state if not already done
                step_description = f"Looking for: {', '.join(target_descriptions)}"
                page_state = self.capture_page_state(step_description, f"Looking for: {', '.join(target_descriptions)}")
                
                # Try to find by analyzing captured elements
                for element in page_state.elements:
                    if self._matches_description(description, element.text_content or ''):
                        resolved_selectors[description] = element.selector or f"{element.tag}:has-text('{element.text_content}')"
                        break
        
        return resolved_selectors
    
    def get_application_guidance(self, scenario_type: str) -> str:
        """Get generic guidance for a scenario type without hardcoded selectors."""
        guidance = f"Application Context: {self.application_context['application_type']} at {self.application_context['base_url']}\n\n"
        
        guidance += "General Guidance:\n"
        guidance += "- Use appropriate selectors based on actual page structure\n"
        guidance += "- Extract functions from the actual test specification content\n"
        guidance += "- Use the exact selectors and patterns found in the spec\n"
        guidance += "- Maintain consistency with existing SDK functions\n"
        
        guidance += "\nImportant Notes:\n"
        for note in self.application_context['important_notes']:
            guidance += f"- {note}\n"
        
        return guidance
    
    def get_context_for_builder(self, current_step: str, accumulated_steps: list = None) -> str:
        """
        Provide context to the builder agent when it needs more information.
        
        Args:
            current_step: The current step being built
            accumulated_steps: List of previously executed steps
            
        Returns:
            str: Contextual information to help the builder agent
        """
        context = f"System Analysis Context for: {current_step}\n\n"
        
        # Add application context
        context += f"Application: {self.application_context['application_type']} at {self.application_context['base_url']}\n\n"
        
        # Add accumulated steps context if available
        if accumulated_steps:
            context += "Previously executed steps:\n"
            for i, step in enumerate(accumulated_steps, 1):
                context += f"{i}. {step}\n"
            context += "\n"
        
        # Add ACTUAL page structure from captured page state
        if hasattr(self, 'last_captured_page_state') and self.last_captured_page_state:
            context += "ACTUAL PAGE STRUCTURE (from captured page state):\n"
            context += f"URL: {self.last_captured_page_state.url}\n"
            context += f"Title: {self.last_captured_page_state.title}\n"
            context += "Available elements:\n"
            for element in self.last_captured_page_state.elements:
                context += f"- {element.tag}"
                if element.text_content:
                    context += f" with text '{element.text_content}'"
                if element.class_name:
                    context += f" (class: {element.class_name})"
                if element.element_type:
                    context += f" (type: {element.element_type})"
                context += "\n"
            context += "\n"
        
        # Add system knowledge if available
        if self.system_knowledge:
            context += "System Knowledge:\n"
            for key, value in self.system_knowledge.items():
                context += f"- {key}: {value}\n"
            context += "\n"
        
        # Add context-aware selector guidance
        context += self._get_context_aware_selector_guidance(current_step)
        
        return context
    
    def _get_context_aware_selector_guidance(self, current_step: str) -> str:
        """Get context-aware selector guidance using LLM analysis."""
        try:
            # Use template to generate the prompt
            prompt = self.template_manager.render_template(
                'agent/context_aware_selector_guidance.j2',
                current_step=current_step
            )
            
            response = self.llm_provider.generate(prompt, "")
            
            # Extract the guidance from the LLM response
            guidance = f"Context-Aware Selector Guidance for: {current_step}\n\n"
            guidance += response
            guidance += "\n\nCRITICAL: Use ONLY the selectors listed above - never invent new ones!\n"
            guidance += "If a required selector is not listed, DO NOT use it.\n"
            
            return guidance
            
        except Exception as e:
            logger.error(f"Failed to get LLM-based selector guidance: {e}")
            # Fallback to basic guidance
            return f"Context-Aware Selector Guidance for: {current_step}\n\n"
            + "Use standard HTML5 selectors like input[name='...'], button[type='submit'], text='...', nav, form, select, textarea\n"
            + "CRITICAL: Never use ID selectors (#anything) or data-testid selectors!"
