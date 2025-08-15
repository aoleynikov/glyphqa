from typing import List, Optional, TYPE_CHECKING, Dict
from pathlib import Path
import logging
import base64

if TYPE_CHECKING:
    from .models import Scenario, Guide

logger = logging.getLogger(__name__)


class ScenarioBuilder:
    def __init__(self, target, config):
        self.target = target
        self.config = config
        self.llm_provider = config.llm
        self.filesystem = None  # Will be initialized when needed
        self.all_guides = {}  # Cache for all loaded guides
    
    def _get_filesystem(self):
        """Get filesystem instance, creating it if needed."""
        if self.filesystem is None:
            from .filesystem import FileSystem
            self.filesystem = FileSystem()
        return self.filesystem
    
    def _load_all_guides(self):
        """Load all available guides into memory."""
        if self.all_guides:  # Already loaded
            return
        
        filesystem = self._get_filesystem()
        guides_dir = '.glyph/guides'
        
        if not filesystem.exists(guides_dir):
            logger.info("No guides directory found, skipping guide loading")
            return
        
        guide_files = filesystem.glob(f"{guides_dir}/*.guide")
        logger.info(f"Loading {len(guide_files)} guides into memory")
        
        for guide_file in guide_files:
            try:
                from .models import Guide
                guide = Guide.from_file(guide_file, filesystem)
                self.all_guides[guide.name] = guide
                logger.debug(f"Loaded guide: {guide.name}")
            except Exception as e:
                logger.warning(f"Failed to load guide {guide_file}: {e}")
        
        logger.info(f"Successfully loaded {len(self.all_guides)} guides")
    
    def build_scenario(self, scenario: 'Scenario') -> str:
        logger.info(f"Building scenario: {scenario.name}")
        
        # Load all guides into memory
        self._load_all_guides()
        
        # Try to load pre-processed actions from guide file
        actions = self._get_actions_from_guide(scenario)
        if not actions:
            # Fallback to generating actions using LLM
            logger.info("No guide file found, generating actions using LLM...")
            actions = scenario.list_actions(self.llm_provider)
        
        logger.info(f"Found {len(actions)} actions:")
        for i, action in enumerate(actions, 1):
            logger.info(f"  {i}. {action}")
        
        spec_file = f'.glyph/tests/{scenario.name}.spec.js'
        if self.filesystem.exists(spec_file):
            self.filesystem.unlink(spec_file)
            logger.info(f"Deleted existing spec: {spec_file}")
        
        current_spec = self._generate_initial_spec()
        implemented_actions = ["Navigate to the root page"]
        
        logger.info(f"Building Playwright test...")
        
        for i, action in enumerate(actions, 1):
            current_spec = self._build_next_action(current_spec, action, implemented_actions)
            implemented_actions.append(action)
        
        self._save_spec(spec_file, current_spec)
        logger.info(f"✅ Saved spec to: {spec_file}")
        
        return current_spec
    
    def _get_actions_from_guide(self, scenario: 'Scenario') -> Optional[List[str]]:
        """Try to load actions from a pre-processed guide file."""
        filesystem = self._get_filesystem()
        guide_file = f'.glyph/guides/{scenario.name}.guide'
        if filesystem.exists(guide_file):
            try:
                from .models import Guide
                guide = Guide.from_file(guide_file, filesystem)
                logger.info(f"Loaded guide: {guide_file}")
                
                # Get flattened actions using the in-memory guides cache
                flattened_actions = guide.get_flattened_actions(self.all_guides, filesystem)
                if len(flattened_actions) != len(guide.actions):
                    logger.info(f"Resolved {len(guide.actions)} actions into {len(flattened_actions)} UI actions")
                
                return flattened_actions
            except Exception as e:
                logger.warning(f"Failed to load guide {guide_file}: {e}")
                return None
        else:
            logger.info(f"No guide file found: {guide_file}")
            return None
    
    def _generate_initial_spec(self) -> str:
        initial_system_prompt = self.target.template_manager.get_playwright_template('initial_spec')
        user_prompt = "Navigate to the root page"
        return self.llm_provider.generate(initial_system_prompt, user_prompt)
    
    def _build_next_action(self, current_spec: str, action: str, implemented_actions: List[str]) -> str:
        debug_spec = self._generate_debug_spec(current_spec)
        page_dump = self._capture_page_state(debug_spec)
        enhanced_prompt = self._generate_enhanced_prompt(current_spec, implemented_actions, page_dump)
        return self._update_spec_with_action(enhanced_prompt, action)
    
    def _generate_debug_spec(self, current_spec: str) -> str:
        debug_system_prompt = self.target.template_manager.get_playwright_template('debug_spec')
        return self.llm_provider.generate(debug_system_prompt, current_spec)
    
    def _capture_page_state(self, debug_spec: str) -> str:
        return self.target.run_debug_spec(debug_spec)
    
    def _generate_enhanced_prompt(self, current_spec: str, implemented_actions: List[str], page_dump: str) -> str:
        actions_list = "\n".join(f"- {action}" for action in implemented_actions)
        return self.target.template_manager.get_playwright_template(
            'enhanced_spec',
            action_count=len(implemented_actions),
            actions_list=actions_list,
            current_spec=current_spec,
            page_dump=page_dump
        )
    
    def _update_spec_with_action(self, enhanced_prompt: str, action: str) -> str:
        screenshot_path = '.glyph/debug-screenshot.png'
        if self.filesystem.exists(screenshot_path):
            screenshot_b64 = self._encode_screenshot(screenshot_path)
            return self.llm_provider.generate(enhanced_prompt, action, screenshot_b64)
        else:
            return self.llm_provider.generate(enhanced_prompt, action)
    
    def _encode_screenshot(self, screenshot_path: str) -> str:
        # Read binary data and encode as base64
        with open(screenshot_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _save_spec(self, spec_file: str, spec_content: str):
        """Save the final spec to file."""
        self.filesystem.write_text(spec_file, spec_content)
