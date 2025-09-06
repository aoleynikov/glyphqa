#!/usr/bin/env python3

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class SystemState:
    """Intelligently manages system state (glyph.md) based on debug spec runs."""
    
    def __init__(self, glyph_dir: Path, llm_provider, template_manager, storage_manager):
        self.glyph_dir = Path(glyph_dir)
        self.storage_manager = storage_manager
        self.current_content = self._load_current_content()
        self.llm_provider = llm_provider
        self.template_manager = template_manager
    
    def _load_current_content(self) -> str:
        """Load current glyph.md content."""
        return self.storage_manager.get_current_content()
    
    def update_from_debug_spec(self, scenario_name: str, action: str, debug_output: str) -> bool:
        """Update glyph.md based on debug spec output. Returns True if updated."""
        logger.info(f"Analyzing debug output for {scenario_name} - {action}")
        
        if self.llm_provider:
            # Use LLM-based analysis
            return self._update_with_llm(scenario_name, action, debug_output)
        else:
            # Use rule-based analysis (fallback)
            return self._update_with_rules(scenario_name, action, debug_output)
    
    def _update_with_llm(self, scenario_name: str, action: str, debug_output: str) -> bool:
        """Update glyph.md using LLM analysis."""
        try:
            # Always use template manager - it's injected via DI
            if not self.template_manager:
                logger.warning("Template manager not available, falling back to rule-based analysis")
                return self._update_with_rules(scenario_name, action, debug_output)
            
            # Use template manager to get the prompt
            system_prompt = self.template_manager.render_template('glyph_md_updater.j2',
                current_glyph_md=self.current_content,
                scenario_name=scenario_name,
                action=action,
                debug_output=debug_output
            )
            
            # Get LLM response
            user_prompt = f"Analyze the debug output for scenario '{scenario_name}' action '{action}'"
            response = self.llm_provider.generate(system_prompt, user_prompt)
            
            # Parse the JSON response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in LLM response")
                return False
            
            analysis = json.loads(json_match.group(1))
            
            if not analysis.get('should_update', False):
                logger.info(f"No update needed: {analysis.get('reason', 'No reason provided')}")
                return False
            
            # Apply the updates
            self._apply_llm_updates(analysis['updates'])
            logger.info(f"Updated glyph.md with {len(analysis['updates'])} updates")
            return True
            
        except Exception as e:
            logger.error(f"LLM-based update failed: {e}")
            logger.info("Falling back to rule-based analysis")
            return self._update_with_rules(scenario_name, action, debug_output)
    
    def _update_with_rules(self, scenario_name: str, action: str, debug_output: str) -> bool:
        """Update glyph.md using rule-based analysis (fallback)."""
        # Parse debug output
        page_data = self._parse_debug_output(debug_output)
        if not page_data:
            logger.warning("Could not parse debug output")
            return False
        
        # Analyze what's new and relevant
        new_insights = self._analyze_for_new_insights(scenario_name, action, page_data)
        
        if not new_insights:
            logger.info("No new insights found - skipping update")
            return False
        
        # Update the document
        self._apply_updates(new_insights)
        logger.info(f"Updated glyph.md with {len(new_insights)} new insights")
        return True
    
    def _parse_debug_output(self, debug_output: str) -> Optional[Dict[str, Any]]:
        """Parse debug output to extract page data."""
        try:
            # Look for JSON data in the debug output
            json_start = debug_output.find('{')
            if json_start == -1:
                return None
            
            # Find the end of the JSON object
            brace_count = 0
            json_end = json_start
            
            for i, char in enumerate(debug_output[json_start:], json_start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end <= json_start:
                return None
            
            json_str = debug_output[json_start:json_end]
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Failed to parse debug output: {e}")
            return None
    
    def _analyze_for_new_insights(self, scenario_name: str, action: str, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze page data for new insights that should be added to glyph.md."""
        new_insights = []
        
        # Extract key information
        url = page_data.get('url', '')
        title = page_data.get('title', '')
        elements = page_data.get('elements', [])
        form_elements = page_data.get('formElements', [])
        navigation_elements = page_data.get('navigationElements', [])
        
        # Check for new page discovery
        page_insight = self._check_for_new_page(url, title, elements)
        if page_insight:
            new_insights.append(page_insight)
        
        # Check for new navigation patterns
        nav_insights = self._check_for_navigation_patterns(url, navigation_elements, action)
        new_insights.extend(nav_insights)
        
        # Check for new form patterns
        form_insights = self._check_for_form_patterns(url, form_elements, action)
        new_insights.extend(form_insights)
        
        # Check for new modal patterns
        modal_insights = self._check_for_modal_patterns(url, page_data, action)
        new_insights.extend(modal_insights)
        
        # Check for new selectors
        selector_insights = self._check_for_new_selectors(elements, action)
        new_insights.extend(selector_insights)
        
        # Check for interaction patterns
        interaction_insights = self._check_for_interaction_patterns(url, elements, action)
        new_insights.extend(interaction_insights)
        
        return new_insights
    
    def _check_for_new_page(self, url: str, title: str, elements: List[Dict]) -> Optional[Dict[str, Any]]:
        """Check if this is a new page that should be documented."""
        if not url or not title:
            return None
        
        # Check if this page is already documented
        if self._page_already_documented(url, title):
            return None
        
        # Determine if this page is worth documenting
        if not self._is_page_worth_documenting(url, title, elements):
            return None
        
        return {
            'type': 'new_page',
            'url': url,
            'title': title,
            'elements_count': len(elements),
            'description': self._generate_page_description(url, title, elements)
        }
    
    def _check_for_navigation_patterns(self, url: str, nav_elements: List[Dict], action: str) -> List[Dict[str, Any]]:
        """Check for new navigation patterns."""
        insights = []
        
        for nav in nav_elements:
            text = nav.get('textContent', '')
            href = nav.get('href', '')
            
            if not text:
                continue
            
            # Check if this navigation pattern is already documented
            if self._navigation_already_documented(text, href):
                continue
            
            # Only document if it's clearly a navigation element
            if self._is_navigation_element(text, href):
                insights.append({
                    'type': 'navigation_pattern',
                    'text': text,
                    'href': href,
                    'url': url,
                    'action': action
                })
        
        return insights
    
    def _check_for_form_patterns(self, url: str, form_elements: List[Dict], action: str) -> List[Dict[str, Any]]:
        """Check for new form patterns."""
        insights = []
        
        if not form_elements:
            return insights
        
        # Check if this form is inside a modal
        forms = form_elements if isinstance(form_elements, list) else []
        for form in forms:
            if isinstance(form, dict) and form.get('isInModal'):
                modal_selector = form.get('modalSelector', '.modal')
                submit_buttons = form.get('submitButtons', [])
                
                insights.append({
                    'type': 'modal_form',
                    'url': url,
                    'action': action,
                    'modalSelector': modal_selector,
                    'submitButtons': submit_buttons,
                    'description': f'Form inside modal {modal_selector} with {len(submit_buttons)} submit button(s)'
                })
        
        # Check if this form pattern is already documented
        if self._form_pattern_already_documented(url, form_elements):
            return insights
        
        # Only document if it's a significant form
        if len(form_elements) >= 2:  # At least 2 form elements to be worth documenting
            insights.append({
                'type': 'form_pattern',
                'url': url,
                'action': action,
                'elements': form_elements
            })
        
        return insights
    
    def _check_for_modal_patterns(self, url: str, page_data: Dict[str, Any], action: str) -> List[Dict[str, Any]]:
        """Check for new modal patterns from enhanced debug output."""
        insights = []
        
        # Check for modals array in page_data
        modals = page_data.get('modals', [])
        if modals:
            for modal in modals:
                if isinstance(modal, dict):
                    modal_selector = modal.get('selector', '')
                    is_visible = modal.get('isVisible', False)
                    role = modal.get('role', 'dialog')
                    forms_in_modal = modal.get('forms', [])
                    submit_buttons = modal.get('submitButtons', [])
                    close_buttons = modal.get('closeButtons', [])
                    
                    if modal_selector and is_visible:
                        insights.append({
                            'type': 'modal_pattern',
                            'url': url,
                            'action': action,
                            'modalSelector': modal_selector,
                            'role': role,
                            'formsCount': len(forms_in_modal),
                            'submitButtons': submit_buttons,
                            'closeButtons': close_buttons,
                            'description': f'Modal {modal_selector} ({role}) with {len(forms_in_modal)} form(s) and {len(submit_buttons)} submit button(s)'
                        })
        
        # Check for forms that are inside modals
        forms = page_data.get('formElements', [])
        if forms:
            for form in forms:
                if isinstance(form, dict) and form.get('isInModal'):
                    modal_selector = form.get('modalSelector', '')
                    submit_buttons = form.get('submitButtons', [])
                    
                    if modal_selector:
                        insights.append({
                            'type': 'modal_form',
                            'url': url,
                            'action': action,
                            'modalSelector': modal_selector,
                            'submitButtons': submit_buttons,
                            'description': f'Form inside modal {modal_selector} with {len(submit_buttons)} submit button(s)'
                        })
        
        # Check for non-form buttons that open modals
        non_form_buttons = page_data.get('nonFormButtons', [])
        if non_form_buttons:
            for button in non_form_buttons:
                if isinstance(button, dict) and button.get('purpose') == 'modal_opener':
                    text = button.get('text', '')
                    # Use the first available selector
                    selectors = button.get('selectors', {})
                    selector = selectors.get('byText') or selectors.get('byType') or 'button'
                    
                    if text and selector:
                        insights.append({
                            'type': 'modal_opener',
                            'url': url,
                            'action': action,
                            'buttonText': text,
                            'buttonSelector': selector,
                            'description': f'Button "{text}" opens modal (use {selector})'
                        })
        
        return insights
    
    def _check_for_new_selectors(self, elements: List[Dict], action: str) -> List[Dict[str, Any]]:
        """Check for new selectors that might be useful."""
        insights = []
        
        for element in elements:
            selectors = element.get('selectors', {})
            text = element.get('textContent', '')
            
            if not selectors or not text:
                continue
            
            # Only document selectors for interactive elements
            if not self._is_interactive_element(element):
                continue
            
            # Check if this selector is already documented
            if self._selector_already_documented(text, selectors):
                continue
            
            # Only document if the selector is reliable
            if self._is_reliable_selector(selectors):
                insights.append({
                    'type': 'new_selector',
                    'text': text,
                    'selectors': selectors,
                    'action': action
                })
        
        return insights
    
    def _check_for_interaction_patterns(self, url: str, elements: List[Dict], action: str) -> List[Dict[str, Any]]:
        """Check for new interaction patterns."""
        insights = []
        
        # Look for patterns in the action that might indicate new interaction methods
        if 'modal' in action.lower() or 'dialog' in action.lower():
            if not self._modal_pattern_already_documented(url):
                insights.append({
                    'type': 'interaction_pattern',
                    'pattern': 'modal_dialog',
                    'url': url,
                    'action': action
                })
        
        if 'wait' in action.lower():
            if not self._wait_pattern_already_documented(url):
                insights.append({
                    'type': 'interaction_pattern',
                    'pattern': 'wait_for_element',
                    'url': url,
                    'action': action
                })
        
        return insights
    
    # Helper methods for checking if information is already documented
    def _page_already_documented(self, url: str, title: str) -> bool:
        """Check if a page is already documented."""
        return f"**URL:** {url}" in self.current_content or f"**Title:** {title}" in self.current_content
    
    def _navigation_already_documented(self, text: str, href: str) -> bool:
        """Check if navigation is already documented."""
        return text in self.current_content
    
    def _form_pattern_already_documented(self, url: str, form_elements: List[Dict]) -> bool:
        """Check if form pattern is already documented."""
        # Simple check - could be more sophisticated
        return url in self.current_content and "form" in self.current_content.lower()
    
    def _selector_already_documented(self, text: str, selectors: Dict) -> bool:
        """Check if selector is already documented."""
        return text in self.current_content
    
    def _modal_pattern_already_documented(self, url: str) -> bool:
        """Check if modal patterns for this URL are already documented."""
        # This is a simplified check - in a real implementation, you'd check glyph.md
        return False
    
    def _form_pattern_already_documented(self, url: str, form_elements: List[Dict]) -> bool:
        """Check if form patterns for this URL are already documented."""
        # This is a simplified check - in a real implementation, you'd check glyph.md
        return False
    
    def _wait_pattern_already_documented(self, url: str) -> bool:
        """Check if wait pattern is already documented."""
        return "wait" in self.current_content.lower() and url in self.current_content
    
    # Helper methods for determining if information is worth documenting
    def _is_page_worth_documenting(self, url: str, title: str, elements: List[Dict]) -> bool:
        """Determine if a page is worth documenting."""
        # Don't document login pages if already documented
        if 'login' in title.lower() and 'login' in self.current_content.lower():
            return False
        
        # Don't document pages with very few elements
        if len(elements) < 3:
            return False
        
        # Don't document error pages
        if 'error' in title.lower() or '404' in title:
            return False
        
        return True
    
    def _is_navigation_element(self, text: str, href: str) -> bool:
        """Determine if an element is a navigation element."""
        nav_keywords = ['dashboard', 'users', 'settings', 'logout', 'login', 'home', 'menu']
        return any(keyword in text.lower() for keyword in nav_keywords) or href.startswith('http')
    
    def _is_interactive_element(self, element: Dict) -> bool:
        """Determine if an element is interactive."""
        tag = element.get('tag', '').lower()
        return tag in ['button', 'a', 'input', 'select']
    
    def _is_reliable_selector(self, selectors: Dict) -> bool:
        """Determine if a selector is reliable."""
        # Prefer text-based selectors
        return 'byText' in selectors or 'byName' in selectors
    
    def _generate_page_description(self, url: str, title: str, elements: List[Dict]) -> str:
        """Generate a description for a page."""
        interactive_count = sum(1 for e in elements if self._is_interactive_element(e))
        form_count = sum(1 for e in elements if e.get('tag', '').lower() in ['input', 'select'])
        
        if form_count > 0:
            return f"Form page with {form_count} form elements and {interactive_count} interactive elements"
        elif interactive_count > 5:
            return f"Interactive page with {interactive_count} interactive elements"
        else:
            return f"Content page with {len(elements)} elements"
    
    def _apply_updates(self, new_insights: List[Dict[str, Any]]):
        """Apply updates to glyph.md."""
        lines = self.current_content.split('\n')
        updated_lines = []
        
        # Find sections to update
        sections = {
            'System Insights': [],
            'Pages Discovered': [],
            'Known Selectors': [],
            'Common Failures & Solutions': []
        }
        
        # Categorize new insights
        for insight in new_insights:
            if insight['type'] == 'new_page':
                sections['Pages Discovered'].append(insight)
            elif insight['type'] == 'new_selector':
                sections['Known Selectors'].append(insight)
            elif insight['type'] in ['navigation_pattern', 'form_pattern', 'interaction_pattern', 'modal_pattern', 'modal_form', 'modal_opener']:
                sections['System Insights'].append(insight)
        
        # Update each section
        current_section = None
        for line in lines:
            updated_lines.append(line)
            
            # Check if we're entering a section
            for section_name in sections.keys():
                if line.strip() == f"## {section_name}":
                    current_section = section_name
                    break
            
            # Add new insights at the end of each section
            if current_section and line.strip() == "" and sections[current_section]:
                for insight in sections[current_section]:
                    updated_lines.append(self._format_insight(insight))
                sections[current_section] = []  # Clear to avoid duplicates
        
        # Update timestamp
        for i, line in enumerate(updated_lines):
            if line.startswith("*Last updated:"):
                updated_lines[i] = f"*Last updated: {datetime.now().isoformat()}*"
                break
        
        # Write updated content
        self.current_content = '\n'.join(updated_lines)
        self.storage_manager.update_content(self.current_content)
    
    def _format_insight(self, insight: Dict[str, Any]) -> str:
        """Format an insight for markdown using templates."""
        if not self.template_manager:
            return self._format_insight_fallback(insight)
        
        try:
            return self.template_manager.render_template('system_state/insight_router.j2',
                insight_type=insight['type'],
                **insight
            )
        except Exception as e:
            logger.warning(f"Template rendering failed for {insight['type']}, using fallback: {e}")
            return self._format_insight_fallback(insight)
    
    def _format_insight_fallback(self, insight: Dict[str, Any]) -> str:
        """Fallback formatting when templates are not available."""
        try:
            return self.template_manager.render_template('system_state/insight_router.j2',
                insight_type=insight['type'],
                **insight
            )
        except Exception as e:
            logger.warning(f"Fallback template rendering failed for {insight['type']}: {e}")
        
        return ""
    
    def _apply_llm_updates(self, updates: List[Dict[str, Any]]):
        """Apply updates from LLM analysis."""
        lines = self.current_content.split('\n')
        updated_lines = []
        
        # Group updates by section
        section_updates = {}
        for update in updates:
            section = update['section']
            if section not in section_updates:
                section_updates[section] = []
            section_updates[section].append(update)
        
        # Process each line and add updates
        current_section = None
        for line in lines:
            updated_lines.append(line)
            
            # Check if we're entering a section
            for section_name in section_updates.keys():
                if line.strip() == f"## {section_name}":
                    current_section = section_name
                    break
            
            # Add updates at the end of each section
            if current_section and line.strip() == "" and current_section in section_updates:
                for update in section_updates[current_section]:
                    if update['type'] == 'add':
                        updated_lines.append(update['content'])
                    elif update['type'] == 'update':
                        # For updates, we'd need more sophisticated logic
                        # For now, just add the content
                        updated_lines.append(update['content'])
                
                # Clear the updates for this section
                section_updates[current_section] = []
        
        # Update timestamp
        for i, line in enumerate(updated_lines):
            if line.startswith("*Last updated:"):
                updated_lines[i] = f"*Last updated: {datetime.now().isoformat()}*"
                break
        
        # Write updated content
        self.current_content = '\n'.join(updated_lines)
        self.storage_manager.update_content(self.current_content)
