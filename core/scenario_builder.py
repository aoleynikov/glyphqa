"""
Clean Scenario Builder - Only contains what the Test Generation Agent needs.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path
import logging
import json
import re
import os
from .exceptions import BuildError, GuideError, FileSystemError, LLMError
from .models import Scenario
from .steps import Step, Action, Check
from .sdk_function import SdkManager, SdkFunction
from .step_mapper import StepMapper, SpecComposer

if TYPE_CHECKING:
    from .models import Scenario

logger = logging.getLogger(__name__)


class DebugSpecManager:
    """Manages debug spec generation and page state capture."""
    
    def __init__(self, llm_provider, template_manager, target):
        self.llm_provider = llm_provider
        self.template_manager = template_manager
        self.target = target
    
    def capture_page_state(self, debug_spec: str, scenario_name: str = None, step_identifier: str = None) -> str:
        """Capture page state using debug spec."""
        try:
            # Save debug spec to temporary file
            debug_file = f'.glyph/tests/debug_{step_identifier or "temp"}.spec.js'
            with open(debug_file, 'w') as f:
                f.write(debug_spec)
            
            # Run the debug spec in headless mode with shorter timeout
            import subprocess
            result = subprocess.run(
                ['npx', 'playwright', 'test', debug_file, '--timeout=5000'],
                cwd='.glyph',
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Clean up debug file
            if os.path.exists(debug_file):
                os.unlink(debug_file)
            
            # Try to extract page state from output regardless of return code
            output = result.stdout + result.stderr
            
            # Look for "Page State:" in the output
            if "Page State:" in output:
                try:
                    # Extract JSON from the output
                    import re
                    json_match = re.search(r'Page State:\s*(\{.*\})', output, re.DOTALL)
                    if json_match:
                        page_state_json = json_match.group(1)
                        return page_state_json
                except Exception as e:
                    logger.warning(f"Failed to parse page state from output: {e}")
            
            if result.returncode == 0:
                return "Page state captured successfully"
            else:
                logger.warning(f"Debug spec execution failed with return code {result.returncode}")
                logger.warning(f"Error output: {result.stderr}")
                return f"Debug failed: {result.stderr[:200]}"
                
        except Exception as e:
            logger.error(f"Failed to capture page state: {e}")
            return f"Error: {str(e)}"




class ScenarioBuilder:
    """
    Clean Scenario Builder - Uses Test Generation Agent for all scenario building.
    """
    
    def __init__(self, target, config, filesystem, system_state, llm_provider, template_manager):
        self.target = target
        self.config = config
        self.filesystem = filesystem
        self.system_state = system_state
        self.llm_provider = llm_provider
        self.template_manager = template_manager
        
        # Initialize components that the agent needs
        self.step_mapper = StepMapper(llm_provider, template_manager, target)
        self.debug_spec_manager = DebugSpecManager(llm_provider, template_manager, target)
        self.sdk_manager = SdkManager(Path('.glyph/sdk'))
    
    def build_scenario(self, scenario: 'Scenario', debug_stop: int = None) -> str:
        """Build scenario using the intelligent test generation agent."""
        from .test_generation_agent import TestGenerationAgent
        
        # Create agent instance
        agent = TestGenerationAgent(self)
        
        # Use agent to build scenario step-by-step
        logger.info(f"Building scenario with intelligent agent: {scenario.name}")
        complete_spec = agent.build_scenario_step_by_step(scenario.name, scenario.text)
        
        # Save the spec
        spec_file = f'.glyph/tests/{scenario.name}{self.target.get_spec_extension()}'
        if self.filesystem.exists(spec_file):
            self.filesystem.unlink(spec_file)
        
        self.filesystem.write_text(spec_file, complete_spec)
        logger.info(f"✅ Saved spec to: {spec_file}")
        
        # SDK update is now handled by the agent
        
        return complete_spec
    
