"""
Circular Reference Analyzer for GlyphQA scenarios.

This module provides lightweight circular reference detection
to prevent infinite dependency loops during scenario builds.
"""

from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class CircularReferenceAnalyzer:
    """Analyzes scenarios for circular dependencies."""
    
    def __init__(self):
        self.scenarios = {}
        self.dependencies = {}
    
    def analyze_scenarios(self, scenarios: Dict[str, any]) -> Tuple[bool, List[str]]:
        """
        Analyze scenarios for circular references.
        
        Args:
            scenarios: Dictionary of scenario data
            
        Returns:
            Tuple of (has_circular_refs, circular_refs_list)
        """
        self.scenarios = scenarios
        self.dependencies = self._extract_dependencies()
        
        # Check for circular references using DFS
        has_circular_refs, circular_refs = self._detect_circular_references()
        
        if has_circular_refs:
            logger.warning(f"Circular references detected: {circular_refs}")
        else:
            logger.info("No circular references found")
            
        return has_circular_refs, circular_refs
    
    def _extract_dependencies(self) -> Dict[str, List[str]]:
        """Extract dependencies from scenarios."""
        dependencies = {}
        
        # Get all valid scenario names
        valid_scenario_names = set(self.scenarios.keys())
        
        for scenario_name, scenario_data in self.scenarios.items():
            # Extract dependencies from scenario data
            deps = scenario_data.get('dependencies', [])
            
            # Filter dependencies to only include actual scenario names
            scenario_deps = []
            for dep in deps:
                # Only include dependencies that are actual scenario names
                if dep in valid_scenario_names:
                    scenario_deps.append(dep)
                # Skip function names and other non-scenario dependencies
            
            dependencies[scenario_name] = scenario_deps
            
        return dependencies
    
    def _detect_circular_references(self) -> Tuple[bool, List[str]]:
        """
        Detect circular references using DFS with three states:
        - WHITE: unvisited
        - GRAY: currently being processed (in current path)
        - BLACK: completely processed
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {scenario: WHITE for scenario in self.dependencies.keys()}
        circular_refs = []
        
        def dfs(scenario: str, path: List[str]) -> bool:
            if color[scenario] == GRAY:
                # Found a cycle - extract the circular path
                cycle_start = path.index(scenario)
                cycle = path[cycle_start:] + [scenario]
                circular_refs.append(" -> ".join(cycle))
                return True
            
            if color[scenario] == BLACK:
                return False
            
            color[scenario] = GRAY
            path.append(scenario)
            
            # Check all dependencies
            for dep in self.dependencies.get(scenario, []):
                if dfs(dep, path):
                    return True
            
            path.pop()
            color[scenario] = BLACK
            return False
        
        # Check all scenarios
        for scenario in self.dependencies.keys():
            if color[scenario] == WHITE:
                if dfs(scenario, []):
                    return True, circular_refs
        
        return len(circular_refs) > 0, circular_refs
    
    def get_build_order(self) -> List[str]:
        """
        Get a safe build order that respects dependencies without circular refs.
        Uses topological sort.
        """
        if self._detect_circular_references()[0]:
            raise ValueError("Cannot determine build order with circular references")
        
        # Topological sort
        in_degree = {scenario: 0 for scenario in self.dependencies.keys()}
        
        # Calculate in-degrees
        for scenario, deps in self.dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Find nodes with no incoming edges
        queue = [scenario for scenario, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            scenario = queue.pop(0)
            result.append(scenario)
            
            # Reduce in-degree for all dependencies
            for dep in self.dependencies.get(scenario, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        return result
