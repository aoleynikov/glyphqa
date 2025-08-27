import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemCatalog:
    """Tracks and catalogs findings about the tested system."""
    
    def __init__(self, filesystem):
        self.filesystem = filesystem
        self.catalog_file = '.glyph/glyph.md'
        self.catalog_data = {
            'last_updated': datetime.now().isoformat(),
            'pages_discovered': {},
            'elements_catalog': {},
            'navigation_patterns': {},
            'form_patterns': {},
            'interaction_patterns': {},
            'known_selectors': {},
            'system_insights': [],
            'site_map': {
                'pages': {},
                'navigation_flows': [],
                'page_hierarchy': {}
            }
        }
        self._load_existing_catalog()
    
    def _load_existing_catalog(self):
        """Load existing catalog if it exists."""
        if self.filesystem.exists(self.catalog_file):
            try:
                content = self.filesystem.read_text(self.catalog_file)
                # Parse the markdown content to extract structured data
                self._parse_markdown_catalog(content)
                logger.info(f"Loaded existing system catalog from {self.catalog_file}")
            except Exception as e:
                logger.warning(f"Failed to load existing catalog: {e}")
    
    def _parse_markdown_catalog(self, content: str):
        """Parse markdown catalog content to extract structured data."""
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                current_section = line[3:].lower().replace(' ', '_')
            elif line.startswith('### ') and current_section:
                subsection = line[4:].lower().replace(' ', '_')
                current_section = f"{current_section}_{subsection}"
            elif line.startswith('- ') and current_section:
                # Parse list items as insights
                if current_section == 'system_insights':
                    self.catalog_data['system_insights'].append(line[2:])
    
    def catalog_page_state(self, url: str, page_data: Dict[str, Any], action_context: str = ""):
        """Catalog findings from a page state."""
        page_key = url.rstrip('/')
        
        if page_key not in self.catalog_data['pages_discovered']:
            self.catalog_data['pages_discovered'][page_key] = {
                'first_seen': datetime.now().isoformat(),
                'url': url,
                'title': page_data.get('title', 'Unknown'),
                'form_elements': [],
                'navigation_elements': [],
                'interaction_elements': [],
                'insights': []
            }
        
        page_info = self.catalog_data['pages_discovered'][page_key]
        page_info['last_seen'] = datetime.now().isoformat()
        
        # Clear previous insights to avoid duplicates
        page_info['insights'] = []
        
        # Catalog form elements
        form_elements = page_data.get('formElements', [])
        for element in form_elements:
            element_key = f"{element.get('tag', 'unknown')}_{element.get('name', 'unnamed')}"
            if element_key not in page_info['form_elements']:
                page_info['form_elements'].append({
                    'tag': element.get('tag'),
                    'name': element.get('name'),
                    'type': element.get('type'),
                    'placeholder': element.get('placeholder'),
                    'text_content': element.get('textContent'),
                    'selectors': element.get('selectors', {})
                })
        
        # Catalog navigation elements
        nav_elements = page_data.get('navigationElements', [])
        for element in nav_elements:
            element_key = f"{element.get('tag', 'unknown')}_{element.get('textContent', 'unnamed')}"
            if element_key not in page_info['navigation_elements']:
                page_info['navigation_elements'].append({
                    'tag': element.get('tag'),
                    'text_content': element.get('textContent'),
                    'href': element.get('href'),
                    'selectors': element.get('selectors', {})
                })
        
        # Generate insights
        insights = self._generate_page_insights(page_data, action_context)
        page_info['insights'].extend(insights)
        
        # Update global patterns
        self._update_global_patterns(page_data)
        
        # Update site map
        self._update_site_map(url, page_data, action_context)
        
        self._save_catalog()
    
    def _generate_page_insights(self, page_data: Dict[str, Any], action_context: str) -> List[str]:
        """Generate insights about the current page state."""
        insights = []
        
        # Analyze form patterns
        form_elements = page_data.get('formElements', [])
        if form_elements:
            input_types = [el.get('type') for el in form_elements if el.get('tag') == 'input']
            if 'text' in input_types and 'password' in input_types:
                insights.append("Login form detected - username and password inputs present")
            
            button_texts = [el.get('textContent') for el in form_elements if el.get('tag') == 'button']
            if 'Login' in button_texts:
                insights.append("Login button detected - form is ready for authentication")
            if 'Save User' in button_texts:
                insights.append("User creation form detected - Save User button present")
        
        # Analyze navigation patterns
        nav_elements = page_data.get('navigationElements', [])
        nav_texts = [el.get('textContent') for el in nav_elements if el.get('textContent')]
        if 'Users' in nav_texts:
            insights.append("User management section accessible via navigation")
        if 'Logout' in nav_texts:
            insights.append("User is authenticated - logout option available")
        
        # Analyze current state
        url = page_data.get('url', '')
        if url.endswith('/') and form_elements:
            insights.append("Root page contains interactive forms - no navigation needed")
        
        return insights
    
    def _update_global_patterns(self, page_data: Dict[str, Any]):
        """Update global interaction patterns."""
        # Track selector patterns
        elements = page_data.get('elements', [])
        for element in elements:
            selectors = element.get('selectors', {})
            for selector_type, selector_value in selectors.items():
                if selector_value:
                    if selector_type not in self.catalog_data['known_selectors']:
                        self.catalog_data['known_selectors'][selector_type] = []
                    if selector_value not in self.catalog_data['known_selectors'][selector_type]:
                        self.catalog_data['known_selectors'][selector_type].append(selector_value)
    
    def _update_site_map(self, url: str, page_data: Dict[str, Any], action_context: str):
        """Update the site map with new page information."""
        page_key = url.rstrip('/')
        title = page_data.get('title', 'Unknown Page')
        
        # Add page to site map
        if page_key not in self.catalog_data['site_map']['pages']:
            self.catalog_data['site_map']['pages'][page_key] = {
                'url': url,
                'title': title,
                'first_discovered': datetime.now().isoformat(),
                'page_type': self._determine_page_type(page_data),
                'available_actions': [],
                'navigation_targets': [],
                'form_actions': []
            }
        
        page_info = self.catalog_data['site_map']['pages'][page_key]
        page_info['last_visited'] = datetime.now().isoformat()
        
        # Update available actions based on page elements
        self._update_page_actions(page_info, page_data)
        
        # Update navigation targets
        self._update_navigation_targets(page_info, page_data)
        
        # Track navigation flows
        if action_context:
            self._track_navigation_flow(page_key, action_context)
    
    def _determine_page_type(self, page_data: Dict[str, Any]) -> str:
        """Determine the type of page based on its content."""
        form_elements = page_data.get('formElements', [])
        nav_elements = page_data.get('navigationElements', [])
        
        # Check for login page
        input_types = [el.get('type') for el in form_elements if el.get('tag') == 'input']
        if 'text' in input_types and 'password' in input_types:
            button_texts = [el.get('textContent') for el in form_elements if el.get('tag') == 'button']
            if 'Login' in button_texts:
                return 'login_page'
        
        # Check for user management page
        nav_texts = [el.get('textContent') for el in nav_elements if el.get('textContent')]
        if 'Users' in nav_texts:
            return 'user_management_page'
        
        # Check for dashboard
        if 'Dashboard' in nav_texts:
            return 'dashboard_page'
        
        # Check for settings page
        if 'Settings' in nav_texts:
            return 'settings_page'
        
        return 'unknown_page'
    
    def _update_page_actions(self, page_info: Dict[str, Any], page_data: Dict[str, Any]):
        """Update available actions for a page."""
        form_elements = page_data.get('formElements', [])
        nav_elements = page_data.get('navigationElements', [])
        
        # Form actions
        form_actions = []
        for element in form_elements:
            if element.get('tag') == 'button':
                text = element.get('textContent', '')
                if text:
                    form_actions.append(f"click_{text.lower().replace(' ', '_')}")
            elif element.get('tag') == 'input':
                name = element.get('name', '')
                if name:
                    form_actions.append(f"fill_{name}")
        
        page_info['form_actions'] = list(set(form_actions))
        
        # Navigation actions
        nav_actions = []
        for element in nav_elements:
            text = element.get('textContent', '')
            if text:
                nav_actions.append(f"navigate_to_{text.lower().replace(' ', '_')}")
        
        page_info['available_actions'] = list(set(form_actions + nav_actions))
    
    def _update_navigation_targets(self, page_info: Dict[str, Any], page_data: Dict[str, Any]):
        """Update navigation targets from a page."""
        nav_elements = page_data.get('navigationElements', [])
        navigation_targets = []
        
        for element in nav_elements:
            text = element.get('textContent', '')
            href = element.get('href', '')
            if text:
                navigation_targets.append({
                    'text': text,
                    'href': href,
                    'element_type': element.get('tag', 'unknown')
                })
        
        page_info['navigation_targets'] = navigation_targets
    
    def _track_navigation_flow(self, current_page: str, action_context: str):
        """Track navigation flows between pages."""
        # Extract navigation intent from action context
        if 'navigate' in action_context.lower() or 'go to' in action_context.lower():
            # This could be enhanced to track actual navigation flows
            # For now, we'll track the action context
            flow_entry = {
                'from_page': current_page,
                'action': action_context,
                'timestamp': datetime.now().isoformat()
            }
            
            if flow_entry not in self.catalog_data['site_map']['navigation_flows']:
                self.catalog_data['site_map']['navigation_flows'].append(flow_entry)
    
    def get_page_summary(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cataloged information about a specific page."""
        page_key = url.rstrip('/')
        return self.catalog_data['pages_discovered'].get(page_key)
    
    def get_system_insights(self) -> List[str]:
        """Get all system insights."""
        return self.catalog_data['system_insights']
    
    def get_site_map_summary(self) -> str:
        """Get a summary of the site map for the prompt."""
        site_map = self.catalog_data['site_map']
        pages = site_map['pages']
        
        if not pages:
            return "No pages discovered yet."
        
        summary_parts = ["Site Map:"]
        
        for url, page_info in pages.items():
            page_type = page_info.get('page_type', 'unknown')
            title = page_info.get('title', 'Unknown')
            available_actions = page_info.get('available_actions', [])
            
            summary_parts.append(f"- {title} ({page_type}): {', '.join(available_actions[:5])}")
        
        return "\n".join(summary_parts)
    
    def add_system_insight(self, insight: str):
        """Add a new system insight."""
        if insight not in self.catalog_data['system_insights']:
            self.catalog_data['system_insights'].append(insight)
            self._save_catalog()
    
    def _save_catalog(self):
        """Save the catalog to markdown file."""
        try:
            # Ensure .glyph directory exists by creating the file in a directory that should exist
            content = self._generate_markdown_content()
            self.filesystem.write_text(self.catalog_file, content)
            logger.info(f"Updated system catalog: {self.catalog_file}")
        except Exception as e:
            logger.error(f"Failed to save system catalog: {e}")
    
    def _generate_markdown_content(self) -> str:
        """Generate markdown content for the catalog."""
        content = [
            "# GlyphQA System Catalog",
            "",
            f"*Last updated: {self.catalog_data['last_updated']}*",
            "",
            "## System Insights",
            ""
        ]
        
        # Add system insights
        for insight in self.catalog_data['system_insights']:
            content.append(f"- {insight}")
        
        content.extend([
            "",
            "## Pages Discovered",
            ""
        ])
        
        # Add page information
        for url, page_info in self.catalog_data['pages_discovered'].items():
            content.extend([
                f"### {page_info['title']}",
                f"**URL:** {page_info['url']}",
                f"**First seen:** {page_info['first_seen']}",
                f"**Last seen:** {page_info['last_seen']}",
                ""
            ])
            
            if page_info['insights']:
                content.append("**Insights:**")
                for insight in page_info['insights']:
                    content.append(f"- {insight}")
                content.append("")
            
            if page_info['form_elements']:
                content.append("**Form Elements:**")
                for element in page_info['form_elements']:
                    content.append(f"- {element['tag']}: {element.get('name', 'unnamed')} ({element.get('type', 'unknown')})")
                content.append("")
            
            if page_info['navigation_elements']:
                content.append("**Navigation Elements:**")
                for element in page_info['navigation_elements']:
                    content.append(f"- {element['tag']}: {element.get('text_content', 'unnamed')}")
                content.append("")
        
        content.extend([
            "## Site Map",
            ""
        ])
        
        # Add site map information
        site_map = self.catalog_data['site_map']
        pages = site_map['pages']
        
        if pages:
            for url, page_info in pages.items():
                content.extend([
                    f"### {page_info['title']}",
                    f"**URL:** {page_info['url']}",
                    f"**Type:** {page_info.get('page_type', 'unknown')}",
                    f"**First discovered:** {page_info['first_discovered']}",
                    f"**Last visited:** {page_info.get('last_visited', 'never')}",
                    ""
                ])
                
                if page_info.get('available_actions'):
                    content.append("**Available Actions:**")
                    for action in page_info['available_actions']:
                        content.append(f"- {action}")
                    content.append("")
                
                if page_info.get('navigation_targets'):
                    content.append("**Navigation Targets:**")
                    for target in page_info['navigation_targets']:
                        content.append(f"- {target['text']} ({target['element_type']})")
                    content.append("")
        else:
            content.append("No pages discovered yet.")
            content.append("")
        
        content.extend([
            "## Known Selectors",
            ""
        ])
        
        # Add selector patterns
        for selector_type, selectors in self.catalog_data['known_selectors'].items():
            content.append(f"### {selector_type}")
            for selector in selectors:
                content.append(f"- `{selector}`")
            content.append("")
        
        return "\n".join(content)
