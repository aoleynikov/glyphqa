from typing import Any, Dict, Optional, List
from pathlib import Path
import logging
import json
from .constants import Constants

logger = logging.getLogger(__name__)


class Scenario:
    def __init__(self, name: str, text: str):
        self.name = name
        self.text = text
    
    @classmethod
    def from_file(cls, filepath: str, filesystem) -> 'Scenario':
        """Create a Scenario from a .glyph file."""
        if not filesystem.exists(filepath):
            raise FileNotFoundError(f"Scenario file not found: {filepath}")
        
        text = filesystem.read_text(filepath)
        name = filesystem.get_stem(filepath)
        
        return cls(name, text)
    
    def to_prompt(self) -> str:
        """Convert scenario to a prompt-friendly format."""
        return f"Scenario: {self.name}\n\n{self.text}"
    
    def list_actions(self, llm_provider, template_manager, scenario_summaries=None) -> List[str]:
        """Generate a list of UI actions from the scenario using LLM."""
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
        
        system_prompt = template_manager.get_scenario_template(Constants.LIST_ACTIONS_TEMPLATE, available_scenarios=scenarios_context)
        
        actions_text = llm_provider.generate(system_prompt, self.text)
        actions = [action.strip() for action in actions_text.split('\n') if action.strip()]
        
        # Validate and fix any self-references or invalid references that might have slipped through
        validated_actions = []
        available_scenario_names = set()
        if scenario_summaries:
            available_scenario_names = set(scenario_summaries.keys())
        
        for action in actions:
            # Check if this action references the current scenario
            if action.startswith(f'[ref: {self.name}]'):
                # Remove the self-reference and keep just the description
                action = action.replace(f'[ref: {self.name}]', '').strip()
                if action:
                    validated_actions.append(action)
            # Check if this action references a non-existent scenario
            elif action.strip().startswith('[ref:') and ']' in action:
                ref_start = action.find('[ref:') + 5
                ref_end = action.find(']')
                scenario_name = action[ref_start:ref_end].strip()
                
                if scenario_name not in available_scenario_names:
                    # Remove the invalid reference and keep just the description
                    logger.warning(f"LLM referenced non-existent scenario '{scenario_name}', fixing to direct action")
                    action = action.replace(f'[ref: {scenario_name}]', '').strip()
                    if action:
                        validated_actions.append(action)
                else:
                    validated_actions.append(action)
            else:
                validated_actions.append(action)
        
        return validated_actions
    
    def parse_steps(self, llm_provider, template_manager, scenario_summaries=None):
        """Parse scenario into structured steps using LLM."""
        from .steps import StepList, Action, Check
        
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
        
        # Use the new step parsing template
        system_prompt = template_manager.get_scenario_template("parse_steps", available_scenarios=scenarios_context)
        
        try:
            steps_json = llm_provider.generate(system_prompt, self.text)
            steps_data = json.loads(steps_json.strip())
            
            step_list = StepList()
            available_scenario_names = set()
            if scenario_summaries:
                available_scenario_names = set(scenario_summaries.keys())
            
            for step_data in steps_data:
                step_type = step_data.get('type', 'action')
                description = step_data.get('description', '')
                
                if step_type == 'action':
                    action_type = step_data.get('action_type', 'click')
                    target = step_data.get('target', '')
                    data = step_data.get('data', {})
                    
                    # Handle scenario references
                    if '[ref:' in description and ']' in description:
                        ref_start = description.find('[ref:') + 5
                        ref_end = description.find(']')
                        scenario_name = description[ref_start:ref_end].strip()
                        
                        if scenario_name not in available_scenario_names:
                            logger.warning(f"LLM referenced non-existent scenario '{scenario_name}', fixing to direct action")
                            description = description.replace(f'[ref: {scenario_name}]', '').strip()
                    
                    step_list.add_action(description, action_type, target, data)
                    
                elif step_type == 'check':
                    check_type = step_data.get('check_type', 'visible')
                    target = step_data.get('target', '')
                    expected = step_data.get('expected', '')
                    
                    step_list.add_check(description, check_type, target, expected, is_explicit=True)
            
            # Add baseline technical checks
            step_list.add_baseline_checks()
            
            return step_list
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse steps JSON: {e}")
            logger.error(f"LLM response: {steps_json}")
            # Fallback to old action-based approach
            actions = self.list_actions(llm_provider, template_manager, scenario_summaries)
            step_list = StepList()
            for action in actions:
                step_list.add_action(action, "click", action)
            step_list.add_baseline_checks()
            return step_list
        except Exception as e:
            logger.error(f"Failed to parse steps: {e}")
            # Fallback to old action-based approach
            actions = self.list_actions(llm_provider, template_manager, scenario_summaries)
            step_list = StepList()
            for action in actions:
                step_list.add_action(action, "click", action)
            step_list.add_baseline_checks()
            return step_list
    
    def summarize(self, llm_provider, template_manager) -> str:
        """Generate a concise summary of the scenario for reference purposes."""
        system_prompt = template_manager.get_scenario_template(Constants.SUMMARIZE_TEMPLATE)
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
    def from_file(cls, filepath: str, filesystem) -> 'Guide':
        """Create a Guide from a .guide file."""
        if not filesystem.exists(filepath):
            raise FileNotFoundError(f"Guide file not found: {filepath}")
        
        import json
        text_content = filesystem.read_text(filepath)
        data = json.loads(text_content)
        
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
            'created_at': None,
            'version': Constants.GUIDE_VERSION
        }
    
    def save(self, filepath: str, filesystem):
        """Save guide to JSON file."""
        import json
        json_content = json.dumps(self.to_dict(), indent=2)
        filesystem.write_text(filepath, json_content)
    
    def to_prompt(self) -> str:
        """Convert guide to a prompt-friendly format."""
        actions_text = '\n'.join(f"{i+1}. {action}" for i, action in enumerate(self.actions))
        return f"Guide: {self.name}\n\nActions:\n{actions_text}"
    
    def resolve_scenario_references(self, all_guides=None, filesystem=None) -> List[str]:
        """Resolve scenario references by expanding them into their constituent actions."""
        if all_guides is None:
            all_guides = {}
        if filesystem is None:
            from .filesystem import FileSystem
            filesystem = FileSystem()
        
        flattened_actions = []
        
        for action in self.actions:
            clean_action = action.lstrip('- ').strip()
            
            if clean_action.startswith('[ref:') and ']' in clean_action:
                ref_start = clean_action.find('[ref:') + 5
                ref_end = clean_action.find(']')
                scenario_name = clean_action[ref_start:ref_end].strip()
                
                referenced_guide = all_guides.get(scenario_name)
                if referenced_guide is None:
                    flattened_actions.append(clean_action)
                    continue
                
                referenced_actions = referenced_guide.resolve_scenario_references(all_guides, filesystem)
                flattened_actions.extend(referenced_actions)
            else:
                flattened_actions.append(clean_action)
        
        return flattened_actions
    
    def get_flattened_actions(self, all_guides=None, filesystem=None) -> List[str]:
        """
        DEPRECATED: Use resolve_scenario_references() instead.
        
        This method name is misleading as it doesn't actually flatten actions
        in the current architecture. The build system now uses imports and
        helper functions instead of flattening.
        """
        import warnings
        warnings.warn(
            "get_flattened_actions() is deprecated. Use resolve_scenario_references() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.resolve_scenario_references(all_guides, filesystem)
