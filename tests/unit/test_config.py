import pytest
import tempfile
import os
from pathlib import Path
from core.config import Config, Connection
from core.target import Target, PlaywrightTarget
from core.llm import LLMProvider


class TestConfig:
    
    def test_config_loads_valid_yaml(self):
        yaml_content = '''
target: playwright
connection:
  url: http://localhost:8080
llm:
  key: sk-test123
  provider: openai
  model: gpt-4o-mini
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.target == 'playwright'
            assert isinstance(config.connection, Connection)
            assert config.connection.url == 'http://localhost:8080'
            assert isinstance(config.llm, LLMProvider)
            # Test that the LLM provider was created correctly
            assert hasattr(config.llm, 'generate')
        finally:
            os.unlink(temp_path)
    
    def test_config_raises_filenotfound_for_missing_file(self):
        with pytest.raises(FileNotFoundError, match='Config file not found'):
            Config('/nonexistent/path/config.yml')
    
    def test_config_raises_valueerror_for_invalid_yaml(self):
        invalid_yaml = '''
project_name: test
invalid: yaml: content: [
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match='Invalid YAML'):
                Config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_config_raises_valueerror_for_non_dict_yaml(self):
        non_dict_yaml = '''
- item1
- item2
- item3
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(non_dict_yaml)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match='Config file must contain a YAML dictionary'):
                Config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_config_get_method_returns_attribute(self):
        yaml_content = '''
target: appium
llm:
  key: test-key
  provider: openai
  model: gpt-4o-mini
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.get('target') == 'appium'
            assert isinstance(config.get('llm'), LLMProvider)
            # Test that the LLM provider was created correctly
            assert hasattr(config.get('llm'), 'generate')
        finally:
            os.unlink(temp_path)
    
    def test_config_get_method_returns_default_for_missing_key(self):
        yaml_content = '''
target: playwright
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.get('missing_key') is None
            assert config.get('missing_key', 'default_value') == 'default_value'
        finally:
            os.unlink(temp_path)
    
    def test_config_repr_shows_attributes(self):
        yaml_content = '''
target: playwright
llm:
  key: test-key
  provider: openai
  model: gpt-4o-mini
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            repr_str = repr(config)
            assert 'playwright' in repr_str
            # The new LLM provider doesn't mask keys in repr, so just check it's there
            assert 'llm' in repr_str
            assert 'filepath' not in repr_str
        finally:
            os.unlink(temp_path)
    
    def test_config_loads_provider_and_connection(self):
        yaml_content = '''
target: appium
connection:
  url: http://localhost:4723
  timeout: 30
llm:
  key: appium-test-key
  provider: openai
  model: gpt-4o
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        
        try:
            config = Config(temp_path)
            assert config.target == 'appium'
            assert isinstance(config.connection, Connection)
            assert config.connection.url == 'http://localhost:4723'
            assert config.connection.timeout == 30
            assert isinstance(config.llm, LLMProvider)
            # Test that the LLM provider was created correctly
            assert hasattr(config.llm, 'generate')
        finally:
            os.unlink(temp_path)





class TestConnection:
    
    def test_connection_with_url_only(self):
        data = {'url': 'http://localhost:8080'}
        conn = Connection(data)
        assert conn.url == 'http://localhost:8080'
    
    def test_connection_with_additional_fields(self):
        data = {
            'url': 'http://localhost:4723',
            'timeout': 30,
            'retries': 3
        }
        conn = Connection(data)
        assert conn.url == 'http://localhost:4723'
        assert conn.timeout == 30
        assert conn.retries == 3
    
    def test_connection_with_default_url(self):
        data = {'timeout': 60}
        conn = Connection(data)
        assert conn.url == 'http://localhost:3000'
        assert conn.timeout == 60
