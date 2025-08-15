import pytest
from unittest.mock import MagicMock, patch, mock_open
from core.models import Scenario, Guide
from core.llm import MockLLMProvider


class TestScenario:
    def test_scenario_constructor_sets_name_and_text(self):
        scenario = Scenario('test_scenario', 'Test scenario content')
        
        assert scenario.name == 'test_scenario'
        assert scenario.text == 'Test scenario content'
    
    def test_to_prompt_returns_formatted_string(self):
        scenario = Scenario('test_name', 'test content')
        prompt = scenario.to_prompt()
        
        assert prompt == 'Scenario: test_name\n\ntest content'
    
    @patch('core.llm.OpenAIProvider')
    def test_list_actions_returns_parsed_actions_from_llm_response(self, mock_openai_provider_class):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = 'Navigate to login page\nEnter username\nEnter password\nClick login button'
        mock_openai_provider_class.return_value = mock_provider
        
        scenario = Scenario('test_name', 'User wants to log into the application')
        actions = scenario.list_actions(mock_provider)
        
        assert actions == ['Navigate to login page', 'Enter username', 'Enter password', 'Click login button']
        mock_provider.generate.assert_called_once()
        call_args = mock_provider.generate.call_args
        assert 'Write the minimal list of UI actions' in call_args[0][0]  # system prompt
        assert call_args[0][1] == 'User wants to log into the application'  # user prompt
    
    @patch('core.llm.OpenAIProvider')
    def test_list_actions_filters_empty_lines(self, mock_openai_provider_class):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = 'Action 1\n\nAction 2\n  \nAction 3'
        mock_openai_provider_class.return_value = mock_provider
        
        scenario = Scenario('test_name', 'Test scenario')
        actions = scenario.list_actions(mock_provider)
        
        assert actions == ['Action 1', 'Action 2', 'Action 3']
    
    @patch('core.llm.OpenAIProvider')
    def test_list_actions_uses_correct_system_prompt(self, mock_openai_provider_class):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = 'Test action'
        mock_openai_provider_class.return_value = mock_provider
        
        scenario = Scenario('test_name', 'Test scenario')
        scenario.list_actions(mock_provider)
        
        call_args = mock_provider.generate.call_args
        system_prompt = call_args[0][0]
        assert 'INCLUDE ONLY:' in system_prompt
        assert 'DO NOT INCLUDE:' in system_prompt
        assert 'Verification steps' in system_prompt
    
    def test_from_file_with_mock_filesystem(self):
        mock_filesystem = MagicMock()
        mock_filesystem.exists.return_value = True
        mock_filesystem.read_text.return_value = 'Test scenario content'
        mock_filesystem.get_stem.return_value = 'test_scenario'
        
        scenario = Scenario.from_file('test_scenario.glyph', mock_filesystem)
        
        assert scenario.name == 'test_scenario'
        assert scenario.text == 'Test scenario content'
        mock_filesystem.exists.assert_called_once_with('test_scenario.glyph')
        mock_filesystem.read_text.assert_called_once_with('test_scenario.glyph')
        mock_filesystem.get_stem.assert_called_once_with('test_scenario.glyph')


class TestGuide:
    def test_guide_constructor_sets_attributes(self):
        guide = Guide('test_guide', 'test.glyph', ['action1', 'action2'])
        
        assert guide.name == 'test_guide'
        assert guide.original_scenario == 'test.glyph'
        assert guide.actions == ['action1', 'action2']
    
    def test_to_dict_returns_correct_structure(self):
        guide = Guide('test_guide', 'test.glyph', ['action1', 'action2'])
        data = guide.to_dict()
        
        expected = {
            'name': 'test_guide',
            'original_scenario': 'test.glyph',
            'actions': ['action1', 'action2'],
            'created_at': None,
            'version': '1.0'
        }
        assert data == expected
    
    def test_to_prompt_returns_formatted_string(self):
        guide = Guide('test_guide', 'test.glyph', ['action1', 'action2'])
        prompt = guide.to_prompt()
        
        expected = 'Guide: test_guide\n\nActions:\n1. action1\n2. action2'
        assert prompt == expected
    
    def test_from_file_with_mock_filesystem(self):
        mock_filesystem = MagicMock()
        mock_filesystem.exists.return_value = True
        mock_filesystem.read_json.return_value = {
            'name': 'test_guide',
            'original_scenario': 'test.glyph',
            'actions': ['action1', 'action2']
        }
        
        guide = Guide.from_file('test_guide.guide', mock_filesystem)
        
        assert guide.name == 'test_guide'
        assert guide.original_scenario == 'test.glyph'
        assert guide.actions == ['action1', 'action2']
        mock_filesystem.exists.assert_called_once_with('test_guide.guide')
        mock_filesystem.read_json.assert_called_once_with('test_guide.guide')
    
    def test_save_with_mock_filesystem(self):
        guide = Guide('test_guide', 'test.glyph', ['action1', 'action2'])
        mock_filesystem = MagicMock()
        
        guide.save('test_guide.guide', mock_filesystem)
        
        expected_data = {
            'name': 'test_guide',
            'original_scenario': 'test.glyph',
            'actions': ['action1', 'action2'],
            'created_at': None,
            'version': '1.0'
        }
        mock_filesystem.write_json.assert_called_once_with('test_guide.guide', expected_data)
