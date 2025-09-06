import yaml
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ConfigurationError
from .constants import Constants

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, data: Dict[str, Any]):
        self.url: str = data.get('url', 'http://localhost:3000')
        for key, value in data.items():
            if key != 'url':
                setattr(self, key, value)
    
    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items()}
        return f'Connection({attrs})'


class Config:
    def __init__(self, filepath: str, filesystem=None):
        self.filepath = filepath
        self.filesystem = filesystem
        self._load_config()
    
    def _load_config(self):
        if not self.filesystem.exists(self.filepath):
            logger.error(Constants.CONFIG_NOT_FOUND.format(self.filepath))
            raise ConfigurationError(Constants.CONFIG_NOT_FOUND.format(self.filepath))
        
        try:
            config_content = self.filesystem.read_text(self.filepath)
            config_data = yaml.safe_load(config_content)
        except yaml.YAMLError as e:
            logger.error(Constants.INVALID_YAML.format(self.filepath, e))
            raise ConfigurationError(Constants.INVALID_YAML.format(self.filepath, e))
        
        if not isinstance(config_data, dict):
            logger.error(Constants.NOT_DICT_YAML.format(self.filepath))
            raise ConfigurationError(Constants.NOT_DICT_YAML.format(self.filepath))
        
        logger.info(Constants.CONFIG_LOADED.format(self.filepath))
        
        for key, value in config_data.items():
            if key == 'llm' and isinstance(value, dict):
                # Store LLM config for later provider creation via DI
                setattr(self, key, value)
            elif key == 'connection' and isinstance(value, dict):
                setattr(self, key, Connection(value))
            else:
                setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)
    
    def get_target_instance(self):
        """Get target instance - this should be handled by DI container now."""
        raise NotImplementedError("get_target_instance should be handled by DI container")
    
    def to_prompt(self) -> str:
        prompt_parts = []
        
        prompt_parts.append(f"Target: {getattr(self, 'target', 'playwright')}")
        
        if hasattr(self, 'connection'):
            prompt_parts.append(f"Application URL: {self.connection.url}")
            prompt_parts.append("Application Type: React SPA with Bootstrap UI")
            prompt_parts.append("Authentication: Username/password login form")
            for attr, value in self.connection.__dict__.items():
                if attr != 'url':
                    prompt_parts.append(f"Connection {attr}: {value}")
        
        if hasattr(self, 'llm'):
            prompt_parts.append(f"LLM Provider: {self.llm.provider}")
            prompt_parts.append(f"LLM Model: {self.llm.model}")
        
        return "\n".join(prompt_parts)
    
    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith('_') and k != 'filepath'}
        return f'Config({attrs})'
