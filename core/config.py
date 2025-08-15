import yaml
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
from .target import Target, PlaywrightTarget
from .llm import create_llm_provider

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
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._load_config()
    
    def _load_config(self):
        config_path = Path(self.filepath)
        if not config_path.exists():
            logger.error(f'Config file not found: {self.filepath}')
            raise FileNotFoundError(f'Config file not found: {self.filepath}')
        
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            logger.error(f'Invalid YAML in config file {self.filepath}: {e}')
            raise ValueError(f'Invalid YAML in config file {self.filepath}: {e}')
        
        if not isinstance(config_data, dict):
            logger.error(f'Config file must contain a YAML dictionary: {self.filepath}')
            raise ValueError(f'Config file must contain a YAML dictionary: {self.filepath}')
        
        logger.info(f'Successfully loaded config from {self.filepath}')
        
        for key, value in config_data.items():
            if key == 'llm' and isinstance(value, dict):
                # Use the new LLM provider abstraction
                setattr(self, key, create_llm_provider(value))
            elif key == 'connection' and isinstance(value, dict):
                setattr(self, key, Connection(value))
            else:
                setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)
    
    def get_target_instance(self) -> Target:
        target_name = getattr(self, 'target', 'playwright')
        if target_name == 'playwright':
            return PlaywrightTarget(self)
        else:
            raise ValueError(f'Unknown target: {target_name}')
    
    def to_prompt(self) -> str:
        prompt_parts = []
        
        target_instance = self.get_target_instance()
        prompt_parts.append(f"Target: {self.target} (v{target_instance.version})")
        
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
