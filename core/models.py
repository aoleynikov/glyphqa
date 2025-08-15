from typing import Any, Dict, Optional, List
from pathlib import Path
import openai
import os
import logging
from .target import Target, PlaywrightTarget
import yaml
import json

logger = logging.getLogger(__name__)


class Scenario:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
    
    @classmethod
    def from_file(cls, filepath: str, filesystem=None) -> 'Scenario':
        """Create a Scenario from a .glyph file."""
        if filesystem is None:
            from .filesystem import FileSystem
            filesystem = FileSystem()
        
        if not filesystem.exists(filepath):
            raise FileNotFoundError(f"Scenario file not found: {filepath}")
        
        text = filesystem.read_text(filepath)
        
        # Extract name from filename (without .glyph extension)
        name = filesystem.get_stem(filepath)
        
        return cls(name, text)
    
    def to_prompt(self) -> str:
        """Convert scenario to a prompt-friendly format."""
        return f"Scenario: {self.name}\n\n{self.text}"
    
    def list_actions(self, llm_provider=None, scenario_summaries=None) -> List[str]:
        """Generate a list of UI actions from the scenario using LLM."""
        # Load the template
        from .templates import TemplateManager
        template_manager = TemplateManager()
        
        # Prepare available scenarios context using summaries
        scenarios_context = []
        if scenario_summaries:
            for scenario_name, summary in scenario_summaries.items():
                # Skip the current scenario to avoid self-reference
                if scenario_name != self.name:
                    scenarios_context.append({
                        'name': scenario_name,
                        'description': summary
                    })
        
        system_prompt = template_manager.get_scenario_template('list_actions', available_scenarios=scenarios_context)
        
        # Use provided LLM provider or create a temporary one
        if llm_provider is None:
            from .llm import OpenAIProvider
            import os
            llm_provider = OpenAIProvider({'key': os.getenv('OPENAI_API_KEY')})
        
        actions_text = llm_provider.generate(system_prompt, self.text)
        actions = [action.strip() for action in actions_text.split('\n') if action.strip()]
        
        return actions
    
    def summarize(self, llm_provider=None) -> str:
        """Generate a concise summary of the scenario for reference purposes."""
        # Load the template
        from .templates import TemplateManager
        template_manager = TemplateManager()
        system_prompt = template_manager.get_scenario_template('summarize')
        
        # Use provided LLM provider or create a temporary one
        if llm_provider is None:
            from .llm import OpenAIProvider
            import os
            llm_provider = OpenAIProvider({'key': os.getenv('OPENAI_API_KEY')})
        
        summary = llm_provider.generate(system_prompt, self.text)
        return summary.strip()
    
    def __repr__(self):
        return f'Scenario(name={self.name}, text_length={len(self.text)})'


class Guide:
    """Represents a pre-processed guide file with action list."""
    
    def __init__(self, name: str, original_scenario: str, actions: List[str]):
        self.name = name
        self.original_scenario = original_scenario
        self.actions = actions
    
    @classmethod
    def from_file(cls, filepath: str, filesystem=None) -> 'Guide':
        """Create a Guide from a .guide file."""
        if filesystem is None:
            from .filesystem import FileSystem
            filesystem = FileSystem()
        
        if not filesystem.exists(filepath):
            raise FileNotFoundError(f"Guide file not found: {filepath}")
        
        data = filesystem.read_json(filepath)
        
        return cls(
            name=data['name'],
            original_scenario=data['original_scenario'],
            actions=data['actions']
        )
    
    def to_dict(self) -> dict:
        """Convert guide to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'original_scenario': self.original_scenario,
            'actions': self.actions,
            'created_at': None,  # Could be added for tracking
            'version': '1.0'
        }
    
    def save(self, filepath: str, filesystem=None):
        """Save guide to JSON file."""
        if filesystem is None:
            from .filesystem import FileSystem
            filesystem = FileSystem()
        
        filesystem.write_json(filepath, self.to_dict())
    
    def to_prompt(self) -> str:
        """Convert guide to a prompt-friendly format."""
        actions_text = '\n'.join(f"{i+1}. {action}" for i, action in enumerate(self.actions))
        return f"Guide: {self.name}\n\nActions:\n{actions_text}"
    
    def get_flattened_actions(self, all_guides=None, filesystem=None) -> List[str]:
        """Recursively flatten all scenario references into a single list of UI actions."""
        if all_guides is None:
            all_guides = {}
        if filesystem is None:
            from .filesystem import FileSystem
            filesystem = FileSystem()
        
        flattened_actions = []
        
        for action in self.actions:
            # Remove the "- " prefix if present
            clean_action = action.lstrip('- ').strip()
            
            if clean_action.startswith('[ref:') and ']' in clean_action:
                # Extract scenario name from reference
                ref_start = clean_action.find('[ref:') + 5
                ref_end = clean_action.find(']')
                scenario_name = clean_action[ref_start:ref_end].strip()
                
                # Get the referenced guide from the provided guides dict
                referenced_guide = all_guides.get(scenario_name)
                if referenced_guide is None:
                    # Guide not found in memory, keep the reference as-is
                    flattened_actions.append(clean_action)
                    continue
                
                # Recursively flatten the referenced guide's actions
                referenced_actions = referenced_guide.get_flattened_actions(all_guides, filesystem)
                flattened_actions.extend(referenced_actions)
            else:
                # Regular action, add it as-is (without the "- " prefix)
                flattened_actions.append(clean_action)
        
        return flattened_actions
