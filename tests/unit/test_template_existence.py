"""
Test that all expected templates exist in the prompts directory.
This ensures we fail fast if templates are missing rather than masking issues with try/except blocks.
"""

import pytest
from pathlib import Path
from core.templates import TemplateManager


class TestTemplateExistence:
    """Test that all required templates exist and can be rendered."""
    
    def setup_method(self):
        """Set up template manager for testing."""
        self.template_manager = TemplateManager()
        # Get the project root directory (two levels up from tests/unit/)
        project_root = Path(__file__).parent.parent.parent
        self.prompts_dir = project_root / 'prompts'
    
    def test_prompts_directory_exists(self):
        """Test that the prompts directory exists."""
        assert self.prompts_dir.exists(), f"Prompts directory not found: {self.prompts_dir}"
        assert self.prompts_dir.is_dir(), f"Prompts path is not a directory: {self.prompts_dir}"
    
    def test_required_templates_exist(self):
        """Test that all required templates exist."""
        required_templates = [
            # Core templates
            'initial_sdk.j2',
            'sdk_updater.j2',
            'pattern_analysis.j2',
            
            # Target-specific templates
            'targets/playwright/action_converter.j2',
            'targets/playwright/initial_spec.j2',
            'targets/playwright/iteration_spec.j2',
            'targets/playwright/debug_spec.j2',
            
            # System state templates
            'system_state/semantic_filter.j2',
            'system_state/minimal_page_state.j2',
            'system_state/insight_router.j2',
            'system_state/initial_content.j2',
            'system_state/form_pattern_insight.j2',
            'system_state/insight_base.j2',
            'system_state/interaction_pattern_insight.j2',
            'system_state/navigation_insight.j2',
            'system_state/page_insight.j2',
            'system_state/selector_insight.j2',
            
            # Scenario templates
            'scenarios/list_actions.j2',
            'scenarios/summarize.j2',
            
            # Other templates
            'glyph_md_updater.j2',
        ]
        
        missing_templates = []
        for template in required_templates:
            template_path = self.prompts_dir / template
            if not template_path.exists():
                missing_templates.append(template)
        
        if missing_templates:
            pytest.fail(f"Missing required templates: {missing_templates}")
    
    def test_template_manager_can_render_all_templates(self):
        """Test that the template manager can render all required templates."""
        test_templates = [
            'initial_sdk.j2',
            'sdk_updater.j2',
            'pattern_analysis.j2',
        ]
        
        for template in test_templates:
            try:
                # Test with minimal context
                if template == 'initial_sdk.j2':
                    content = self.template_manager.render_template(
                        template, 
                        llm_analysis="Test analysis", 
                        guide_count=1
                    )
                elif template == 'sdk_updater.j2':
                    content = self.template_manager.render_template(
                        template,
                        current_sdk="// Test SDK",
                        scenario_name="test_scenario",
                        spec_content="// Test spec",
                        sdk_design="# Test design"
                    )
                elif template == 'pattern_analysis.j2':
                    content = self.template_manager.render_template(
                        template,
                        guide_data='{"test": "data"}'
                    )
                else:
                    content = self.template_manager.render_template(template)
                
                assert content is not None, f"Template {template} rendered None"
                assert len(content) > 0, f"Template {template} rendered empty content"
                
            except Exception as e:
                pytest.fail(f"Failed to render template {template}: {e}")
    
    def test_template_manager_can_render_core_templates(self):
        """Test that template manager can render core templates with basic context."""
        # Test that we can render the core templates without errors
        # This ensures the templates are syntactically valid and have required variables
        
        # Test initial_sdk.j2
        content = self.template_manager.render_template(
            'initial_sdk.j2',
            llm_analysis="Test analysis",
            guide_count=5
        )
        assert content is not None and len(content) > 0
        
        # Test sdk_updater.j2
        content = self.template_manager.render_template(
            'sdk_updater.j2',
            current_sdk="// Test SDK",
            scenario_name="test_scenario",
            spec_content="// Test spec",
            sdk_design="# Test design"
        )
        assert content is not None and len(content) > 0
        
        # Test pattern_analysis.j2
        content = self.template_manager.render_template(
            'pattern_analysis.j2',
            guide_data='{"test": "data"}'
        )
        assert content is not None and len(content) > 0
