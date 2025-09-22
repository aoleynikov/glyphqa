"""
Dependency Injection Container for GlyphQA.

Manages service instantiation and dependency resolution.
"""

from typing import Dict, Any, Optional, Type, Callable
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from .filesystem import FileSystem
from .config import Config
from .llm import LLMProvider, create_llm_provider
from .templates import TemplateManager
from .target import Target
from .scenario_builder import ScenarioBuilder

from .hash_caching import HashCachingSystem

logger = logging.getLogger(__name__)


class Container:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(self, name: str, factory: Callable, singleton: bool = True):
        """Register a service factory."""
        self._factories[name] = factory
        if not singleton:
            # For non-singletons, we don't cache the instance
            pass
    
    def register_instance(self, name: str, instance: Any):
        """Register a pre-created instance."""
        self._singletons[name] = instance
    
    def get(self, name: str) -> Any:
        """Get a service instance, creating it if needed."""
        # Check if we already have a singleton instance
        if name in self._singletons:
            return self._singletons[name]
        
        # Check if we have a factory
        if name in self._factories:
            factory = self._factories[name]
            instance = factory(self)
            
            # Cache singleton instances
            if name not in self._services:  # This indicates it's a singleton
                self._singletons[name] = instance
            
            return instance
        
        raise KeyError(f"Service '{name}' not registered")
    
    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._factories or name in self._singletons


class GlyphQAContainer(Container):
    """GlyphQA-specific dependency injection container."""
    
    def __init__(self, config_path: str = 'glyph.config.yml'):
        super().__init__()
        self.config_path = config_path
        self._setup_services()
    
    def _setup_services(self):
        """Register all services with their dependencies."""
        
        # Core services
        self.register('config', self._create_config)
        self.register('filesystem', self._create_filesystem)
        self.register('template_manager', self._create_template_manager)
        self.register('llm_provider', self._create_llm_provider)
        
        # Target services
        self.register('target', self._create_target)
        
        # Builder services
        self.register('scenario_builder', self._create_scenario_builder)

        self.register('hash_caching', self._create_hash_caching)
    
    def _create_config(self, container: Container) -> Config:
        """Create configuration instance."""
        filesystem = container.get('filesystem')
        return Config(self.config_path, filesystem)
    
    def _create_filesystem(self, container: Container) -> FileSystem:
        """Create filesystem instance."""
        return FileSystem()
    
    def _create_template_manager(self, container: Container) -> TemplateManager:
        """Create template manager instance."""
        return TemplateManager()
    
    def _create_llm_provider(self, container: Container) -> LLMProvider:
        """Create LLM provider instance."""
        config = container.get('config')
        llm_config = config.get('llm', {})
        return create_llm_provider(llm_config)
    
    def _create_target(self, container: Container) -> Target:
        """Create target instance."""
        config = container.get('config')
        target_name = config.get('target', 'playwright')
        if target_name == 'playwright':
            from .target import PlaywrightTarget
            return PlaywrightTarget(config)
        else:
            from .exceptions import ConfigurationError
            raise ConfigurationError(f"Unknown target: {target_name}")
    
    def _create_scenario_builder(self, container: Container) -> ScenarioBuilder:
        """Create scenario builder instance."""
        target = container.get('target')
        config = container.get('config')
        filesystem = container.get('filesystem')
        llm_provider = container.get('llm_provider')
        template_manager = container.get('template_manager')
        return ScenarioBuilder(target, config, filesystem, None, llm_provider, template_manager)
    

    
    def _create_hash_caching(self, container: Container) -> HashCachingSystem:
        """Create hash caching system instance."""
        glyph_dir = Path('.glyph')
        filesystem = container.get('filesystem')
        return HashCachingSystem(glyph_dir, filesystem)
    
    


def create_container(config_path: str = 'glyph.config.yml') -> GlyphQAContainer:
    """Create and configure the GlyphQA container."""
    return GlyphQAContainer(config_path)
