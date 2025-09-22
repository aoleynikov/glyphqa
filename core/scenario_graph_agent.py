"""
Agent-based Scenario Graph Builder - Analyzes scenarios directly without guide files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Set, Optional
from .scenario_graph import ScenarioGraph, ScenarioNode
from .test_generation_agent import TestGenerationAgent
from .llm_circular_reference_detector import LLMCircularReferenceDetector

logger = logging.getLogger(__name__)


class ScenarioGraphAgent:
    """
    Agent-based scenario graph builder that analyzes scenarios directly.
    Eliminates the need for guide files by using the agent's intelligence.
    """
    
    def __init__(self, agent: TestGenerationAgent):
        self.agent = agent
        self.circular_ref_detector = LLMCircularReferenceDetector(agent.llm_provider, agent.template_manager)
    
    def build_graph_from_scenarios(self, scenarios_dir: str = 'scenarios') -> ScenarioGraph:
        """
        Build scenario graph directly from .glyph files using agent analysis.
        
        Args:
            scenarios_dir: Directory containing .glyph scenario files
            
        Returns:
            ScenarioGraph with dependencies and topological ordering
        """
        logger.info(f"Building scenario graph from {scenarios_dir} using agent analysis")
        
        graph = ScenarioGraph()
        scenario_files = list(Path(scenarios_dir).glob("*.glyph"))
        
        if not scenario_files:
            logger.warning(f"No .glyph files found in {scenarios_dir}")
            return graph
        
        logger.info(f"Found {len(scenario_files)} scenario files")
        
        # First pass: Load all scenarios and analyze dependencies
        scenario_data = {}
        for scenario_file in scenario_files:
            try:
                scenario_name = scenario_file.stem
                scenario_text = scenario_file.read_text()
                
                # Use agent to analyze dependencies
                dependencies = self.agent.analyze_scenario_dependencies(scenario_name, scenario_text)
                
                scenario_data[scenario_name] = {
                    'file': str(scenario_file),
                    'text': scenario_text,
                    'dependencies': dependencies
                }
                
                logger.info(f"Analyzed {scenario_name}: depends on {dependencies}")
                
            except Exception as e:
                logger.error(f"Failed to analyze {scenario_file}: {e}")
        
        # Skip circular reference detection for now since scenarios are independent
        logger.info("⚠️  Skipping circular reference detection - scenarios are independent")
        
        # Second pass: Add scenarios to graph with validated dependencies
        for scenario_name, data in scenario_data.items():
            # Validate dependencies exist
            valid_dependencies = []
            for dep in data['dependencies']:
                if dep in scenario_data:
                    valid_dependencies.append(dep)
                else:
                    logger.warning(f"Scenario {scenario_name} depends on {dep} which doesn't exist")
            
            # Add to graph
            graph.add_scenario(
                name=scenario_name,
                dependencies=valid_dependencies
            )
        
        # Build topological ordering
        try:
            build_layers = graph.get_build_layers()
            logger.info(f"✅ Scenario graph built successfully")
            logger.info(f"Scenario Graph: {len(graph.nodes)} scenarios")
            logger.info(f"Build layers: {len(build_layers)}")
            
            for i, layer in enumerate(build_layers, 1):
                logger.info(f"  Layer {i}: {layer}")
            
            # Log dependencies
            for name, node in graph.nodes.items():
                if node.dependencies:
                    logger.info(f"  {name} depends on: {node.dependencies}")
                else:
                    logger.info(f"  {name} (no dependencies)")
                    
        except Exception as e:
            logger.error(f"Failed to build topological ordering: {e}")
        
        return graph
    
    def get_optimal_build_order(self, scenarios_dir: str = 'scenarios') -> List[str]:
        """
        Get the optimal build order for scenarios, respecting dependencies
        and preventing circular references.
        
        Args:
            scenarios_dir: Directory containing .glyph scenario files
            
        Returns:
            List of scenario names in optimal build order
        """
        logger.info(f"🔍 Determining optimal build order for scenarios in {scenarios_dir}")
        
        scenario_files = list(Path(scenarios_dir).glob("*.glyph"))
        if not scenario_files:
            logger.warning(f"No .glyph files found in {scenarios_dir}")
            return []
        
        # Load and analyze scenarios
        scenario_data = {}
        for scenario_file in scenario_files:
            try:
                scenario_name = scenario_file.stem
                scenario_text = scenario_file.read_text()
                dependencies = self.agent.analyze_scenario_dependencies(scenario_name, scenario_text)
                
                scenario_data[scenario_name] = {
                    'file': str(scenario_file),
                    'text': scenario_text,
                    'dependencies': dependencies
                }
                
            except Exception as e:
                logger.error(f"Failed to analyze {scenario_file}: {e}")
        
        # Check for circular references using LLM
        scenario_content = {}
        for scenario_name, data in scenario_data.items():
            scenario_content[scenario_name] = data['text']
        
        has_circular_refs, circular_refs = self.circular_ref_detector.detect_circular_references(scenario_content)
        
        if has_circular_refs:
            logger.error("❌ Circular references detected!")
            for ref in circular_refs:
                logger.error(f"  Circular reference: {ref}")
            raise ValueError(f"Circular references detected: {circular_refs}")
        
        # For now, return alphabetical order since we don't have explicit dependencies
        # In the future, we could enhance this to use LLM for dependency analysis
        build_order = sorted(scenario_data.keys())
        logger.info(f"✅ Build order determined: {build_order}")
        return build_order
    
    def get_dependency_subtree(self, graph: ScenarioGraph, target_scenario: str) -> List[str]:
        """
        Get all scenarios that the target scenario depends on (recursively).
        
        Args:
            graph: The scenario graph
            target_scenario: The target scenario name
            
        Returns:
            List of all scenarios in the dependency subtree
        """
        dependencies = set()
        to_process = [target_scenario]
        
        while to_process:
            current = to_process.pop(0)
            deps = graph.get_dependencies_for_scenario(current)
            for dep in deps:
                if dep not in dependencies:
                    dependencies.add(dep)
                    to_process.append(dep)
        
        return list(dependencies)
    
    def filter_build_layers_for_target(self, graph: ScenarioGraph, target_scenario: str) -> List[List[str]]:
        """
        Filter build layers to only include scenarios needed for the target.
        
        Args:
            graph: The scenario graph
            target_scenario: The target scenario name
            
        Returns:
            Filtered build layers containing only relevant scenarios
        """
        # Get all dependencies recursively
        dependency_subtree = set(self.get_dependency_subtree(graph, target_scenario))
        dependency_subtree.add(target_scenario)
        
        logger.info(f"🎯 Building dependency subtree for {target_scenario}: {', '.join(sorted(dependency_subtree))}")
        
        # Filter build layers to only include dependency subtree
        all_layers = graph.get_build_layers()
        filtered_layers = []
        
        for layer in all_layers:
            layer_deps = [s for s in layer if s in dependency_subtree]
            if layer_deps:
                filtered_layers.append(layer_deps)
            else:
                logger.info(f"⏭️  Skipping layer {', '.join(layer)} (not in dependency subtree)")
        
        logger.info(f"📊 Filtered to {len(filtered_layers)} dependency layers")
        return filtered_layers
