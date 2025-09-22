"""
Scenario Graph - Manages scenario dependencies and build order.
"""

import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScenarioNode:
    """Represents a scenario in the dependency graph."""
    name: str
    dependencies: List[str]
    dependents: List[str]
    built: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.dependents is None:
            self.dependents = []


class ScenarioGraph:
    """Manages scenario dependencies and build order."""
    
    def __init__(self):
        self.nodes: Dict[str, ScenarioNode] = {}
    
    def add_scenario(self, name: str, dependencies: List[str] = None):
        """Add a scenario to the graph."""
        if dependencies is None:
            dependencies = []
        
        # Create or update the node
        if name in self.nodes:
            self.nodes[name].dependencies = dependencies
        else:
            self.nodes[name] = ScenarioNode(
                name=name,
                dependencies=dependencies,
                dependents=[]
            )
        
        # Update dependents for each dependency
        for dep in dependencies:
            if dep not in self.nodes:
                self.nodes[dep] = ScenarioNode(
                    name=dep,
                    dependencies=[],
                    dependents=[]
                )
            if name not in self.nodes[dep].dependents:
                self.nodes[dep].dependents.append(name)
    
    def get_dependencies_for_scenario(self, scenario_name: str) -> List[str]:
        """Get all dependencies for a scenario."""
        if scenario_name not in self.nodes:
            return []
        return self.nodes[scenario_name].dependencies.copy()
    
    def get_build_layers(self) -> List[List[str]]:
        """Get build layers in topological order (dependencies first)."""
        layers = []
        remaining = set(self.nodes.keys())
        
        while remaining:
            # Find scenarios with no unresolved dependencies
            current_layer = []
            for scenario in list(remaining):
                deps = self.get_dependencies_for_scenario(scenario)
                if all(dep not in remaining for dep in deps):
                    current_layer.append(scenario)
            
            if not current_layer:
                # Circular dependency or error
                logger.warning(f"Circular dependency detected. Remaining scenarios: {remaining}")
                # Add all remaining scenarios to the last layer
                current_layer = list(remaining)
            
            layers.append(current_layer)
            remaining -= set(current_layer)
        
        return layers
    
    def mark_scenario_built(self, scenario_name: str):
        """Mark a scenario as built."""
        if scenario_name in self.nodes:
            self.nodes[scenario_name].built = True
    
    def visualize_graph(self, focus_scenario: str = None) -> str:
        """Create a text visualization of the dependency graph."""
        lines = []
        lines.append("Scenario Dependency Graph")
        lines.append("=" * 30)
        
        if focus_scenario and focus_scenario in self.nodes:
            lines.append(f"\nFocus: {focus_scenario}")
            lines.append(f"Dependencies: {', '.join(self.get_dependencies_for_scenario(focus_scenario))}")
            lines.append(f"Dependents: {', '.join(self.nodes[focus_scenario].dependents)}")
        else:
            # Show all scenarios
            for name, node in self.nodes.items():
                status = "✓" if node.built else "○"
                lines.append(f"{status} {name}")
                if node.dependencies:
                    lines.append(f"  depends on: {', '.join(node.dependencies)}")
                if node.dependents:
                    lines.append(f"  required by: {', '.join(node.dependents)}")
        
        return "\n".join(lines)
    
    def visualize_dependency_tree(self, scenario_name: str) -> str:
        """Create a tree visualization of dependencies for a specific scenario."""
        if scenario_name not in self.nodes:
            return f"Scenario '{scenario_name}' not found in graph"
        
        lines = []
        lines.append(f"Dependency Tree for: {scenario_name}")
        lines.append("=" * 40)
        
        def build_tree(name: str, visited: Set[str], depth: int = 0):
            if name in visited:
                lines.append("  " * depth + f"↳ {name} (circular dependency)")
                return
            
            visited.add(name)
            status = "✓" if self.nodes[name].built else "○"
            lines.append("  " * depth + f"{status} {name}")
            
            for dep in self.get_dependencies_for_scenario(name):
                build_tree(dep, visited.copy(), depth + 1)
        
        build_tree(scenario_name, set())
        return "\n".join(lines)
