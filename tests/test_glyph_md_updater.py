#!/usr/bin/env python3

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from core.glyph_md_updater import GlyphMdUpdater


class TestGlyphMdUpdater:
    """Test the glyph.md updater functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.glyph_dir = Path(self.temp_dir) / ".glyph"
        self.glyph_dir.mkdir(parents=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_initial_content_creation(self):
        """Test that initial content is created when glyph.md doesn't exist."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Check that initial content was created
        assert "# GlyphQA System Catalog" in updater.current_content
        assert "## System Insights" in updater.current_content
        assert "## Pages Discovered" in updater.current_content
        assert "## Known Selectors" in updater.current_content
    
    def test_parse_debug_output(self):
        """Test parsing debug output to extract page data."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Create sample debug output
        debug_output = """Current URL: http://localhost:3000/
Page Title: Login Page
Page State: {
  "url": "http://localhost:3000/",
  "title": "Login Page",
  "elements": [
    {
      "tag": "input",
      "type": "text",
      "textContent": "Username",
      "selectors": {
        "byName": "[name=\\"username\\"]"
      }
    }
  ],
  "formElements": [
    {
      "tag": "input",
      "type": "text"
    }
  ]
}"""
        
        page_data = updater._parse_debug_output(debug_output)
        
        assert page_data is not None
        assert page_data['url'] == "http://localhost:3000/"
        assert page_data['title'] == "Login Page"
        assert len(page_data['elements']) == 1
        assert len(page_data['formElements']) == 1
    
    def test_new_page_detection(self):
        """Test detection of new pages worth documenting."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Test a page that should be documented
        page_data = {
            'url': 'http://localhost:3000/dashboard',
            'title': 'Dashboard',
            'elements': [
                {'tag': 'button', 'textContent': 'Create User'},
                {'tag': 'a', 'textContent': 'Users'},
                {'tag': 'div', 'textContent': 'Welcome'}
            ]
        }
        
        insight = updater._check_for_new_page(
            page_data['url'], 
            page_data['title'], 
            page_data['elements']
        )
        
        assert insight is not None
        assert insight['type'] == 'new_page'
        assert insight['url'] == 'http://localhost:3000/dashboard'
        assert insight['title'] == 'Dashboard'
    
    def test_page_not_worth_documenting(self):
        """Test that pages with few elements are not documented."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Test a page with too few elements
        page_data = {
            'url': 'http://localhost:3000/error',
            'title': 'Error Page',
            'elements': [
                {'tag': 'div', 'textContent': 'Error'}
            ]
        }
        
        insight = updater._check_for_new_page(
            page_data['url'], 
            page_data['title'], 
            page_data['elements']
        )
        
        assert insight is None
    
    def test_new_selector_detection(self):
        """Test detection of new selectors."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        elements = [
            {
                'tag': 'button',
                'textContent': 'Create User',
                'selectors': {
                    'byText': 'text="Create User"',
                    'byName': '[name="create"]'
                }
            }
        ]
        
        insights = updater._check_for_new_selectors(elements, "click create user button")
        
        assert len(insights) == 1
        assert insights[0]['type'] == 'new_selector'
        assert insights[0]['text'] == 'Create User'
        assert 'byText' in insights[0]['selectors']
    
    def test_navigation_pattern_detection(self):
        """Test detection of navigation patterns."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        nav_elements = [
            {
                'textContent': 'Users',
                'href': 'http://localhost:3000/users'
            }
        ]
        
        insights = updater._check_for_navigation_patterns(
            'http://localhost:3000/dashboard',
            nav_elements,
            'navigate to users'
        )
        
        assert len(insights) == 1
        assert insights[0]['type'] == 'navigation_pattern'
        assert insights[0]['text'] == 'Users'
    
    def test_form_pattern_detection(self):
        """Test detection of form patterns."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        form_elements = [
            {'tag': 'input', 'type': 'text'},
            {'tag': 'input', 'type': 'password'},
            {'tag': 'button', 'type': 'submit'}
        ]
        
        insights = updater._check_for_form_patterns(
            'http://localhost:3000/login',
            form_elements,
            'fill login form'
        )
        
        assert len(insights) == 1
        assert insights[0]['type'] == 'form_pattern'
        assert len(insights[0]['elements']) == 3
    
    def test_interaction_pattern_detection(self):
        """Test detection of interaction patterns."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        elements = []
        
        insights = updater._check_for_interaction_patterns(
            'http://localhost:3000/dashboard',
            elements,
            'wait for modal to appear'
        )
        
        assert len(insights) == 2  # Both modal and wait patterns detected
        assert insights[0]['type'] == 'interaction_pattern'
        assert insights[0]['pattern'] == 'modal_dialog'
    
    def test_duplicate_detection(self):
        """Test that duplicate information is not added."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Add some content to simulate existing documentation
        existing_content = """# GlyphQA System Catalog
*Last updated: 2025-01-27T10:30:00*

## System Insights

## Pages Discovered
### Dashboard
**URL:** http://localhost:3000/dashboard
**Description:** Interactive page with 5 interactive elements
**Elements:** 5 total

## Known Selectors
### Create User
**Selectors:** `byText=text="Create User"`
**Context:** click create user button

## Common Failures & Solutions
"""
        
        updater.current_content = existing_content
        
        # Test that a duplicate page is not added
        page_data = {
            'url': 'http://localhost:3000/dashboard',
            'title': 'Dashboard',
            'elements': [{'tag': 'div'}]
        }
        
        insight = updater._check_for_new_page(
            page_data['url'],
            page_data['title'],
            page_data['elements']
        )
        
        assert insight is None  # Should not add duplicate
    
    def test_update_application(self):
        """Test that updates are properly applied to glyph.md."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Create sample insights
        new_insights = [
            {
                'type': 'new_page',
                'url': 'http://localhost:3000/dashboard',
                'title': 'Dashboard',
                'elements_count': 5,
                'description': 'Interactive page with 5 interactive elements'
            },
            {
                'type': 'new_selector',
                'text': 'Create User',
                'selectors': {'byText': 'text="Create User"'},
                'action': 'click create user button'
            }
        ]
        
        # Apply updates
        updater._apply_updates(new_insights)
        
        # Check that content was updated
        updated_content = updater.glyph_md_file.read_text()
        assert 'Dashboard' in updated_content
        assert 'Create User' in updated_content
        assert 'text="Create User"' in updated_content
    
    def test_complete_update_flow(self):
        """Test the complete update flow from debug output."""
        updater = GlyphMdUpdater(self.glyph_dir)
        
        # Create sample debug output
        debug_output = """Current URL: http://localhost:3000/dashboard
Page Title: Dashboard
Page State: {
  "url": "http://localhost:3000/dashboard",
  "title": "Dashboard",
  "elements": [
    {
      "tag": "button",
      "textContent": "Create User",
      "selectors": {
        "byText": "text=\\"Create User\\""
      }
    },
    {
      "tag": "a",
      "textContent": "Users",
      "href": "http://localhost:3000/users"
    }
  ],
  "formElements": [],
  "navigationElements": [
    {
      "textContent": "Users",
      "href": "http://localhost:3000/users"
    }
  ]
}"""
        
        # Test the complete update
        updated = updater.update_from_debug_spec(
            'create_user',
            'navigate to dashboard',
            debug_output
        )
        
        assert updated is True
        
        # Check that content was written
        assert updater.glyph_md_file.exists()
        content = updater.glyph_md_file.read_text()
        assert 'Create User' in content  # This should be added as a selector
    
    def test_llm_based_update(self):
        """Test LLM-based update functionality."""
        from unittest.mock import Mock
        
        # Create a mock LLM provider
        mock_llm = Mock()
        mock_llm.generate.return_value = '''```json
{
  "should_update": true,
  "reason": "New navigation pattern discovered",
  "updates": [
    {
      "section": "System Insights",
      "type": "add",
      "content": "### New Navigation Pattern\\n**Pattern:** Dashboard navigation\\n**Context:** User management flow",
      "reason": "Helps understand navigation structure"
    }
  ],
  "insights": [
    "Dashboard has consistent navigation structure",
    "User management accessible via navigation menu"
  ]
}
```'''
        
        updater = GlyphMdUpdater(self.glyph_dir, llm_provider=mock_llm)
        
        debug_output = """Current URL: http://localhost:3000/dashboard
Page Title: Dashboard
Page State: {
  "url": "http://localhost:3000/dashboard",
  "title": "Dashboard",
  "elements": [
    {
      "tag": "a",
      "textContent": "Users",
      "href": "http://localhost:3000/users"
    }
  ]
}"""
        
        updated = updater.update_from_debug_spec('test_scenario', 'navigate to dashboard', debug_output)
        
        assert updated is True
        mock_llm.generate.assert_called_once()
        
        # Check that content was updated
        content = updater.glyph_md_file.read_text()
        assert 'New Navigation Pattern' in content
        assert 'Dashboard navigation' in content


if __name__ == "__main__":
    pytest.main([__file__])
