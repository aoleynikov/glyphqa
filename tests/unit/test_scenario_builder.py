import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import shutil
from core.scenario_builder import ScenarioBuilder
from core.llm import MockLLMProvider
from core.target import PlaywrightTarget


class FakeLLMProvider:
    """A fake LLM provider that returns realistic responses based on prompts."""
    
    def __init__(self):
        # Dictionary mapping prompt patterns to responses
        self.responses = {
            # Initial spec generation
            'Navigate to the root page': 'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n});',
            
            # Debug spec generation (adds console.log statements)
            'console.log': 'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  console.log("Current URL:", await page.url());\n  console.log("Page Title:", await page.title());\n});',
            
            # Enhanced spec responses for different actions
            'Fill email field with admin@example.com': 'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.fill("input[type=\\"email\\"]", "admin@example.com");\n});',
            
            'Fill password field with admin123': 'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.fill("input[type=\\"email\\"]", "admin@example.com");\n  await page.fill("input[type=\\"password\\"]", "admin123");\n});',
            
            'Click login button': 'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n  await page.fill("input[type=\\"email\\"]", "admin@example.com");\n  await page.fill("input[type=\\"password\\"]", "admin123");\n  await page.click("button[type=\\"submit\\"]");\n});',
        }
        
        # Track call history for verification
        self.call_history = []
    
    def generate(self, system_prompt: str, user_prompt: str, image_data=None):
        """Generate a response based on the user prompt."""
        # Record the call
        call_info = {
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'image_data': image_data is not None
        }
        self.call_history.append(call_info)
        
        # Find the best matching response
        for pattern, response in self.responses.items():
            if pattern in user_prompt:
                return response
        
        # Fallback response if no pattern matches
        return 'import { test, expect } from "@playwright/test";\ntest("test", async ({ page }) => {\n  await page.goto("/");\n});'
    
    def get_call_history(self):
        """Get the history of all calls made to this provider."""
        return self.call_history


class TestScenarioBuilder:
    """Test the core build_scenario flow with real templates and file system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a real PlaywrightTarget so we get real template_manager
        self.mock_config = Mock()
        self.real_target = PlaywrightTarget(self.mock_config)
        
        # Create a fake LLM provider with realistic responses
        self.fake_llm = FakeLLMProvider()
        self.mock_config.llm = self.fake_llm
        
        # Create the builder with the real target
        self.builder = ScenarioBuilder(self.real_target, self.mock_config)
        
        # Mock scenario with predefined actions
        self.mock_scenario = Mock()
        self.mock_scenario.name = 'test_scenario'
        self.mock_scenario.list_actions.return_value = [
            'Fill email field with admin@example.com',
            'Fill password field with admin123',
            'Click login button'
        ]
    
    def test_build_scenario_flow(self):
        """Test the complete build_scenario flow using real templates and file system."""
        # Create a temporary .glyph directory structure
        glyph_dir = Path('.glyph')
        tests_dir = glyph_dir / 'tests'
        tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Define the expected spec file path
        expected_spec_file = tests_dir / 'test_scenario.spec.js'
        
        # Mock the run_debug_spec method to avoid actual test execution
        self.real_target.run_debug_spec = Mock(return_value='Current URL: http://localhost:3000\nPage Title: React App')
        
        try:
            # Execute the build process
            result = self.builder.build_scenario(self.mock_scenario)
            
            # Verify the final result contains all expected actions
            assert 'await page.goto("/")' in result
            assert 'await page.fill("input[type=\\"email\\"]", "admin@example.com")' in result
            assert 'await page.fill("input[type=\\"password\\"]", "admin123")' in result
            assert 'await page.click("button[type=\\"submit\\"]")' in result
            
            # Verify the LLM was called the expected number of times
            # 1 initial + (3 actions * 2 calls each: debug + enhanced) = 7 total calls
            assert len(self.fake_llm.get_call_history()) == 7
            
            # Verify the call sequence
            calls = self.fake_llm.get_call_history()
            
            # Initial spec call - should use real template
            initial_call = calls[0]
            assert 'Navigate to the root page' in initial_call['user_prompt']
            # The system prompt should contain actual template content
            system_prompt = initial_call['system_prompt']
            assert 'Playwright' in system_prompt
            assert 'test.describe' in system_prompt
            
            # Debug spec calls (odd indices: 1, 3, 5) - should use real debug template
            debug_calls = [calls[1], calls[3], calls[5]]
            for debug_call in debug_calls:
                debug_system_prompt = debug_call['system_prompt']
                assert 'console.log' in debug_system_prompt
                assert 'page.url()' in debug_system_prompt
            
            # Enhanced spec calls (even indices: 2, 4, 6) - should use real enhanced template
            enhanced_calls = [calls[2], calls[4], calls[6]]
            for enhanced_call in enhanced_calls:
                enhanced_system_prompt = enhanced_call['system_prompt']
                assert 'CRITICAL DECISION LOGIC' in enhanced_system_prompt
                assert 'current spec' in enhanced_system_prompt
                # The page_dump variable gets rendered, so we check for the actual content instead
                assert 'Current URL: http://localhost:3000' in enhanced_system_prompt
            
            # Verify action-specific user prompts
            assert calls[2]['user_prompt'] == 'Fill email field with admin@example.com'
            assert calls[4]['user_prompt'] == 'Fill password field with admin123'
            assert calls[6]['user_prompt'] == 'Click login button'
            
            # Verify target methods were called correctly
            assert self.real_target.run_debug_spec.call_count == 3  # Once per action
            
            # Verify the actual spec file was created
            assert expected_spec_file.exists()
            
            # Verify the file content matches our final result
            with open(expected_spec_file, 'r') as f:
                file_content = f.read()
                assert 'await page.goto("/")' in file_content
                assert 'await page.fill("input[type=\\"email\\"]", "admin@example.com")' in file_content
                assert 'await page.fill("input[type=\\"password\\"]", "admin123")' in file_content
                assert 'await page.click("button[type=\\"submit\\"]")' in file_content
            
        finally:
            # Clean up using shutil.rmtree for robust cleanup
            if glyph_dir.exists():
                shutil.rmtree(glyph_dir)
