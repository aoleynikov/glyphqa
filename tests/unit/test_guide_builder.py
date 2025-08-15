import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import shutil
import json

from core.models import Guide
from core.scenario_builder import ScenarioBuilder
from core.llm import MockLLMProvider


class TestGuideBuilder:
    """Test the build process using guide files instead of glyphs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock()
        self.mock_target = MagicMock()
        
        # Create a more sophisticated mock LLM provider
        self.mock_llm = MagicMock()
        self.mock_config.llm = self.mock_llm
        
        # Create a mock template manager
        self.mock_template_manager = MagicMock()
        self.mock_template_manager.get_playwright_template.side_effect = lambda template, **kwargs: f"Template: {template}"
        self.mock_target.template_manager = self.mock_template_manager
        
        # Create a mock filesystem
        self.mock_filesystem = MagicMock()
        self.mock_filesystem.exists.return_value = True
        self.mock_filesystem.read_json.return_value = {
            'name': 'test_guide',
            'original_scenario': 'test_guide.glyph',
            'actions': [
                'Navigate to login page',
                'Type "admin" in username field',
                'Type "admin_password" in password field',
                'Click login button'
            ],
            'created_at': None,
            'version': '1.0'
        }
        self.mock_filesystem.write_text.return_value = None
        
        # Create the builder with mocked dependencies
        self.builder = ScenarioBuilder(self.mock_target, self.mock_config)
        self.builder.filesystem = self.mock_filesystem
        
        # Create test guide
        self.test_guide = Guide(
            name='test_guide',
            original_scenario='test_guide.glyph',
            actions=[
                'Navigate to login page',
                'Type "admin" in username field',
                'Type "admin_password" in password field',
                'Click login button'
            ]
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up any real files that might have been created
        if Path('.glyph').exists():
            shutil.rmtree(Path('.glyph'))
    
    def test_build_from_guide_loads_actions_correctly(self):
        """Test that building from a guide loads actions correctly."""
        # Mock the guide loading
        with patch.object(self.builder, '_get_actions_from_guide') as mock_get_actions:
            mock_get_actions.return_value = self.test_guide.actions
            
            # Mock the LLM responses for the build process
            self.mock_llm.generate.side_effect = [
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  console.log("Current URL:", await page.url());\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.goto("/login");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n  await page.fill("input[name=\\"password\\"]", "admin_password");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n  await page.fill("input[name=\\"password\\"]", "admin_password");\n  await page.click("button[type=\\"submit\\"]");\n});'
            ]
            
            # Mock the target's run_debug_spec method
            self.mock_target.run_debug_spec.return_value = 'Current URL: http://localhost:3000\nPage Title: Login Page'
            
            # Mock screenshot handling
            with patch('builtins.open', mock_open(read_data=b'fake_screenshot_data')):
                with patch('base64.b64encode') as mock_b64encode:
                    mock_b64encode.return_value.decode.return_value = 'fake_base64_data'
                    
                    # Create a mock scenario (we'll use the guide name as scenario name)
                    mock_scenario = MagicMock()
                    mock_scenario.name = 'test_guide'
                    
                    # Build the scenario
                    result = self.builder.build_scenario(mock_scenario)
                    
                    # Verify the guide was loaded
                    mock_get_actions.assert_called_once()
                    
                    # Verify the spec was generated with all actions
                    assert 'await page.goto("/")' in result
                    assert 'await page.goto("/login")' in result
                    assert 'await page.fill("input[name=\\"username\\"]", "admin")' in result
                    assert 'await page.fill("input[name=\\"password\\"]", "admin_password")' in result
                    assert 'await page.click("button[type=\\"submit\\"]")' in result
    
    def test_build_from_guide_with_scenario_references(self):
        """Test building from a guide that contains scenario references."""
        # Create a guide with scenario references
        guide_with_refs = Guide(
            name='complex_test',
            original_scenario='complex_test.glyph',
            actions=[
                '[ref: login_as_admin] login as admin user',
                'Navigate to settings page',
                '[ref: user_management] create new user',
                'Verify user appears in list'
            ]
        )
        
        with patch.object(self.builder, '_get_actions_from_guide') as mock_get_actions:
            mock_get_actions.return_value = guide_with_refs.actions
            
            # Mock LLM responses
            self.mock_llm.generate.side_effect = [
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  console.log("Current URL:", await page.url());\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  // Execute login_as_admin scenario\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n  await page.fill("input[name=\\"password\\"]", "admin_password");\n  await page.click("button[type=\\"submit\\"]");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  // Execute login_as_admin scenario\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n  await page.fill("input[name=\\"password\\"]", "admin_password");\n  await page.click("button[type=\\"submit\\"]");\n  await page.goto("/settings");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  // Execute login_as_admin scenario\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n  await page.fill("input[name=\\"password\\"]", "admin_password");\n  await page.click("button[type=\\"submit\\"]");\n  await page.goto("/settings");\n  // Execute user_management scenario\n  await page.click("button:has-text(\\"Add User\\")");\n  await page.fill("input[name=\\"name\\"]", "Test User");\n  await page.fill("input[name=\\"email\\"]", "test@example.com");\n  await page.click("button:has-text(\\"Save\\")");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  // Execute login_as_admin scenario\n  await page.goto("/login");\n  await page.fill("input[name=\\"username\\"]", "admin");\n  await page.fill("input[name=\\"password\\"]", "admin_password");\n  await page.click("button[type=\\"submit\\"]");\n  await page.goto("/settings");\n  // Execute user_management scenario\n  await page.click("button:has-text(\\"Add User\\")");\n  await page.fill("input[name=\\"name\\"]", "Test User");\n  await page.fill("input[name=\\"email\\"]", "test@example.com");\n  await page.click("button:has-text(\\"Save\\")");\n  await expect(page.locator("text=Test User")).toBeVisible();\n});'
            ]
            
            self.mock_target.run_debug_spec.return_value = 'Current URL: http://localhost:3000\nPage Title: Dashboard'
            
            # Mock screenshot handling
            with patch('builtins.open', mock_open(read_data=b'fake_screenshot_data')):
                with patch('base64.b64encode') as mock_b64encode:
                    mock_b64encode.return_value.decode.return_value = 'fake_base64_data'
                    
                    mock_scenario = MagicMock()
                    mock_scenario.name = 'complex_test'
                    
                    result = self.builder.build_scenario(mock_scenario)
                    
                    # Verify scenario references are handled
                    assert '// Execute login_as_admin scenario' in result
                    assert '// Execute user_management scenario' in result
                    assert 'await expect(page.locator("text=Test User")).toBeVisible()' in result
    
    def test_build_from_guide_fallback_to_llm(self):
        """Test that build falls back to LLM when guide file is not found."""
        with patch.object(self.builder, '_get_actions_from_guide') as mock_get_actions:
            mock_get_actions.return_value = None  # No guide file found
            
            # Mock scenario with list_actions method
            mock_scenario = MagicMock()
            mock_scenario.name = 'missing_guide'
            mock_scenario.list_actions.return_value = [
                'Navigate to login page',
                'Click login button'
            ]
            
            # Mock LLM responses for fallback
            self.mock_llm.generate.side_effect = [
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  console.log("Current URL:", await page.url());\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.goto("/login");\n});',
                'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.goto("/login");\n  await page.click("button:has-text(\\"Login\\")");\n});'
            ]
            
            self.mock_target.run_debug_spec.return_value = 'Current URL: http://localhost:3000\nPage Title: Login'
            
            # Mock screenshot handling
            with patch('builtins.open', mock_open(read_data=b'fake_screenshot_data')):
                with patch('base64.b64encode') as mock_b64encode:
                    mock_b64encode.return_value.decode.return_value = 'fake_base64_data'
                    
                    result = self.builder.build_scenario(mock_scenario)
                    
                    # Verify fallback was used
                    mock_scenario.list_actions.assert_called_once_with(self.mock_config.llm)
                    
                    # Verify spec was generated
                    assert 'await page.goto("/")' in result
                    assert 'await page.goto("/login")' in result
                    assert 'await page.click("button:has-text(\\"Login\\")")' in result
    
    def test_get_flattened_actions_resolves_references(self):
        """Test that get_flattened_actions properly resolves scenario references."""
        # Create a guide with scenario references
        guide_with_refs = Guide(
            name='complex_test',
            original_scenario='complex_test.glyph',
            actions=[
                '[ref: login_as_admin] login as admin user',
                'Navigate to settings page',
                '[ref: user_management] create new user',
                'Verify user appears in list'
            ]
        )
        
        # Create the referenced guides
        login_guide = Guide(
            name='login_as_admin',
            original_scenario='login_as_admin.glyph',
            actions=[
                'Navigate to login page',
                'Type "admin" in username field',
                'Type "admin_password" in password field',
                'Click login button'
            ]
        )
        
        user_mgmt_guide = Guide(
            name='user_management',
            original_scenario='user_management.glyph',
            actions=[
                'Click "Add User" button',
                'Fill in name field with "Test User"',
                'Fill in email field with "test@example.com"',
                'Click "Save" button'
            ]
        )
        
        # Create a dictionary of all guides
        all_guides = {
            'login_as_admin': login_guide,
            'user_management': user_mgmt_guide
        }
        
        # Get flattened actions
        flattened_actions = guide_with_refs.get_flattened_actions(all_guides)
        
        # Verify the flattened actions
        expected_actions = [
            # From login_as_admin reference
            'Navigate to login page',
            'Type "admin" in username field',
            'Type "admin_password" in password field',
            'Click login button',
            # Direct action
            'Navigate to settings page',
            # From user_management reference
            'Click "Add User" button',
            'Fill in name field with "Test User"',
            'Fill in email field with "test@example.com"',
            'Click "Save" button',
            # Direct action
            'Verify user appears in list'
        ]
        
        assert flattened_actions == expected_actions
    
    def test_get_flattened_actions_handles_missing_references(self):
        """Test that get_flattened_actions handles missing references gracefully."""
        guide_with_missing_ref = Guide(
            name='test_guide',
            original_scenario='test_guide.glyph',
            actions=[
                'Navigate to login page',
                '[ref: missing_guide] do something',
                'Click login button'
            ]
        )
        
        # Get flattened actions with empty guides dict
        flattened_actions = guide_with_missing_ref.get_flattened_actions({})
        
        # Should keep the reference as-is when guide is missing
        expected_actions = [
            'Navigate to login page',
            '[ref: missing_guide] do something',
            'Click login button'
        ]
        
        assert flattened_actions == expected_actions
    
    def test_get_flattened_actions_handles_nested_references(self):
        """Test that get_flattened_actions handles nested references correctly."""
        # Create nested references: A -> B -> C
        guide_c = Guide(
            name='guide_c',
            original_scenario='guide_c.glyph',
            actions=[
                'Click button C',
                'Verify C result'
            ]
        )
        
        guide_b = Guide(
            name='guide_b',
            original_scenario='guide_b.glyph',
            actions=[
                'Click button B',
                '[ref: guide_c] execute C scenario',
                'Verify B result'
            ]
        )
        
        guide_a = Guide(
            name='guide_a',
            original_scenario='guide_a.glyph',
            actions=[
                'Click button A',
                '[ref: guide_b] execute B scenario',
                'Verify A result'
            ]
        )
        
        all_guides = {
            'guide_b': guide_b,
            'guide_c': guide_c
        }
        
        # Get flattened actions for guide_a
        flattened_actions = guide_a.get_flattened_actions(all_guides)
        
        expected_actions = [
            'Click button A',
            # From guide_b reference
            'Click button B',
            # From guide_c reference (nested in guide_b)
            'Click button C',
            'Verify C result',
            'Verify B result',
            'Verify A result'
        ]
        
        assert flattened_actions == expected_actions
