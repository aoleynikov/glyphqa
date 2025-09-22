"""
LLM-based Circular Reference Detector for GlyphQA scenarios.

This module uses the LLM to analyze all scenarios at once and detect
circular dependencies, which is more efficient than complex algorithms.
"""

import logging
from typing import Dict, List, Tuple, Any
from .llm import LLMProvider
from .templates import TemplateManager

logger = logging.getLogger(__name__)


class LLMCircularReferenceDetector:
    """Uses LLM to detect circular references in scenarios."""
    
    def __init__(self, llm: LLMProvider, template_manager: TemplateManager):
        self.llm = llm
        self.template_manager = template_manager
    
    def detect_circular_references(self, scenarios: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Use LLM to detect circular references in scenarios.
        
        Args:
            scenarios: Dictionary of scenario_name -> scenario_content
            
        Returns:
            Tuple of (has_circular_refs, circular_refs_list)
        """
        if not scenarios:
            return False, []
        
        try:
            # Render the template with actual scenario names
            prompt = self.template_manager.render_template(
                'agent/circular_reference_analysis.j2',
                scenarios=scenarios,
                actual_scenario_names=list(scenarios.keys())
            )
            
            # Get LLM analysis
            response = self.llm.generate(
                system_prompt="You are an expert at analyzing scenario dependencies and detecting circular references.",
                user_prompt=prompt
            )
            
            # Parse the response
            has_circular_refs, circular_refs = self._parse_response(response)
            
            if has_circular_refs:
                logger.warning(f"Circular references detected: {circular_refs}")
            else:
                logger.info("No circular references found")
                
            return has_circular_refs, circular_refs
            
        except Exception as e:
            logger.error(f"Failed to analyze circular references: {e}")
            # Fallback: assume no circular references
            return False, []
    
    
    def _parse_response(self, response: str) -> Tuple[bool, List[str]]:
        """Parse the LLM response to extract circular reference information."""
        lines = response.strip().split('\n')
        has_circular_refs = False
        circular_refs = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('CIRCULAR_REFERENCES:'):
                has_circular_refs = line.split(':', 1)[1].strip().lower() == 'true'
            elif line.startswith('CHAINS:'):
                # Skip the CHAINS: header
                continue
            elif line and line != 'none' and not line.startswith('CIRCULAR_REFERENCES:'):
                # This is a circular reference chain
                circular_refs.append(line.strip())
        
        return has_circular_refs, circular_refs
