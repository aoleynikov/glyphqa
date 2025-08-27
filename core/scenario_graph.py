#!/usr/bin/env python3

import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class ScenarioNode:
    """Represents a scenario in the dependency graph."""
    name: str
    dependencies: List[str] = None
    actions: List[str] = None
    glyph_file: str = None
    built: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.actions is None:
            self.actions = []


class ScenarioGraph:
    """Manages scenario dependencies and topological sorting."""
    
    def __init__(self):
        self.nodes: Dict[str, ScenarioNode] = {}
        self.adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)
    
    def add_scenario(self, name: str, dependencies: List[str] = None, actions: List[str] = None, glyph_file: str = None):
        """Add a scenario to the graph."""
        if dependencies is None:
            dependencies = []
        
        node = ScenarioNode(
            name=name,
            dependencies=dependencies,
            actions=actions or [],
            glyph_file=glyph_file
        )
        
        self.nodes[name] = node
        
        # Build adjacency lists
        for dep in dependencies:
            self.adjacency_list[dep].add(name)  # dep -> name
            self.reverse_adjacency[name].add(dep)  # name -> dep
        
        logger.debug(f"Added scenario: {name} with dependencies: {dependencies}")
    
    def validate_graph(self) -> Tuple[bool, List[str]]:
        """Validate the graph for cycles and missing dependencies."""
        errors = []
        
        # Check for missing dependencies
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    errors.append(f"Scenario '{name}' depends on missing scenario '{dep}'")
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_name: str) -> bool:
            if node_name in rec_stack:
                return True
            if node_name in visited:
                return False
            
            visited.add(node_name)
            rec_stack.add(node_name)
            
            for neighbor in self.adjacency_list[node_name]:
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node_name)
            return False
        
        # Check for cycles starting from each node
        for node_name in self.nodes:
            if node_name not in visited:
                if has_cycle(node_name):
                    errors.append(f"Circular dependency detected involving '{node_name}'")
                    break
        
        return len(errors) == 0, errors
    
    def topological_sort(self) -> List[str]:
        """Perform topological sort to get build order (leaves to root)."""
        # Kahn's algorithm
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for name in self.nodes:
            in_degree[name] = len(self.reverse_adjacency[name])
        
        # Find all nodes with no incoming edges (leaves)
        queue = deque([name for name in self.nodes if in_degree[name] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Remove current node and update in-degrees
            for neighbor in self.adjacency_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if we processed all nodes
        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles - cannot perform topological sort")
        
        return result
    
    def get_build_layers(self) -> List[List[str]]:
        """Get scenarios organized by build layers (leaves to root)."""
        build_order = self.topological_sort()
        layers = []
        current_layer = []
        
        for scenario_name in build_order:
            # Check if all dependencies are in previous layers
            node = self.nodes[scenario_name]
            if all(dep in [s for layer in layers for s in layer] for dep in node.dependencies):
                current_layer.append(scenario_name)
            else:
                # Start new layer
                if current_layer:
                    layers.append(current_layer)
                current_layer = [scenario_name]
        
        if current_layer:
            layers.append(current_layer)
        
        return layers
    
    def get_dependencies_for_scenario(self, scenario_name: str) -> List[str]:
        """Get all dependencies for a specific scenario."""
        if scenario_name not in self.nodes:
            return []
        
        node = self.nodes[scenario_name]
        return node.dependencies.copy()
    
    def get_dependents_of_scenario(self, scenario_name: str) -> List[str]:
        """Get all scenarios that depend on the given scenario."""
        return list(self.adjacency_list[scenario_name])
    
    def mark_scenario_built(self, scenario_name: str):
        """Mark a scenario as built."""
        if scenario_name in self.nodes:
            self.nodes[scenario_name].built = True
            logger.debug(f"Marked scenario '{scenario_name}' as built")
    
    def get_unbuilt_dependencies(self, scenario_name: str) -> List[str]:
        """Get dependencies that haven't been built yet."""
        if scenario_name not in self.nodes:
            return []
        
        node = self.nodes[scenario_name]
        return [dep for dep in node.dependencies if not self.nodes[dep].built]
    
    def print_graph_info(self):
        """Print information about the graph structure."""
        logger.info(f"Scenario Graph: {len(self.nodes)} scenarios")
        
        build_layers = self.get_build_layers()
        logger.info(f"Build layers: {len(build_layers)}")
        
        for i, layer in enumerate(build_layers):
            logger.info(f"  Layer {i+1}: {layer}")
        
        # Print dependencies
        for name, node in self.nodes.items():
            if node.dependencies:
                logger.info(f"  {name} depends on: {node.dependencies}")
            else:
                logger.info(f"  {name} (no dependencies)")
    
    def visualize_graph(self, target_scenario: str = None) -> str:
        """Generate a simple text-based visualization of the graph."""
        if target_scenario and target_scenario not in self.nodes:
            return f"Scenario '{target_scenario}' not found in graph"
        
        lines = []
        lines.append("📊 Scenario Dependency Graph")
        lines.append("=" * 50)
        
        if target_scenario:
            lines.append(f"Focus: {target_scenario}")
            lines.append("")
            return self._visualize_scenario_subgraph(target_scenario, lines)
        
        # Full graph visualization
        build_layers = self.get_build_layers()
        
        for i, layer in enumerate(build_layers):
            lines.append(f"Layer {i+1}:")
            for scenario in layer:
                node = self.nodes[scenario]
                if node.dependencies:
                    deps_str = ", ".join(node.dependencies)
                    lines.append(f"  {scenario} ← [{deps_str}]")
                else:
                    lines.append(f"  {scenario} (root)")
            lines.append("")
        
        # Show dependency relationships
        lines.append("Dependency Relationships:")
        lines.append("-" * 30)
        
        for name, node in self.nodes.items():
            if node.dependencies:
                for dep in node.dependencies:
                    lines.append(f"{dep} → {name}")
        
        return "\n".join(lines)
    
    def _visualize_scenario_subgraph(self, target_scenario: str, lines: List[str]) -> str:
        """Visualize the subgraph for a specific scenario."""
        node = self.nodes[target_scenario]
        
        # Show dependencies (what this scenario needs)
        if node.dependencies:
            lines.append("Dependencies (required):")
            for dep in node.dependencies:
                lines.append(f"  {dep}")
            lines.append("")
        else:
            lines.append("Dependencies: None (root scenario)")
            lines.append("")
        
        # Show dependents (what depends on this scenario)
        dependents = self.get_dependents_of_scenario(target_scenario)
        if dependents:
            lines.append("Dependents (scenarios that need this):")
            for dep in dependents:
                lines.append(f"  {dep}")
            lines.append("")
        else:
            lines.append("Dependents: None (leaf scenario)")
            lines.append("")
        
        # Show build path
        lines.append("Build Path:")
        build_order = self.topological_sort()
        target_index = build_order.index(target_scenario)
        
        for i, scenario in enumerate(build_order):
            if i == target_index:
                lines.append(f"  {i+1}. {scenario} ← TARGET")
            elif i < target_index:
                lines.append(f"  {i+1}. {scenario} ← REQUIRED")
            else:
                lines.append(f"  {i+1}. {scenario}")
        
        return "\n".join(lines)
    
    def visualize_dependency_tree(self, scenario_name: str, max_depth: int = 3) -> str:
        """Generate a tree-like visualization of dependencies for a scenario."""
        if scenario_name not in self.nodes:
            return f"Scenario '{scenario_name}' not found"
        
        lines = []
        lines.append(f"🌳 Dependency Tree for: {scenario_name}")
        lines.append("=" * 50)
        
        visited = set()
        self._build_dependency_tree(scenario_name, lines, visited, depth=0, max_depth=max_depth)
        
        return "\n".join(lines)
    
    def _build_dependency_tree(self, scenario_name: str, lines: List[str], visited: Set[str], depth: int, max_depth: int):
        """Recursively build the dependency tree visualization."""
        if depth > max_depth or scenario_name in visited:
            return
        
        visited.add(scenario_name)
        indent = "  " * depth
        node = self.nodes[scenario_name]
        
        if depth == 0:
            lines.append(f"{indent}└── {scenario_name}")
        else:
            lines.append(f"{indent}├── {scenario_name}")
        
        if node.dependencies and depth < max_depth:
            for i, dep in enumerate(node.dependencies):
                if i == len(node.dependencies) - 1:
                    # Last dependency
                    self._build_dependency_tree(dep, lines, visited, depth + 1, max_depth)
                else:
                    # Not the last dependency
                    self._build_dependency_tree(dep, lines, visited, depth + 1, max_depth)


class ScenarioGraphBuilder:
    """Builds scenario graph from guide files."""
    
    def __init__(self, guides_dir: Path):
        self.guides_dir = Path(guides_dir)
        self.graph = ScenarioGraph()
    
    def build_graph_from_guides(self) -> ScenarioGraph:
        """Build scenario graph from existing guide files."""
        import json
        
        guide_files = list(self.guides_dir.glob("*.guide"))
        logger.info(f"Building graph from {len(guide_files)} guide files")
        
        for guide_file in guide_files:
            try:
                with open(guide_file, 'r') as f:
                    guide_data = json.load(f)
                
                scenario_name = guide_data.get('name', guide_file.stem)
                actions = guide_data.get('actions', [])
                
                # Extract dependencies from actions
                dependencies = self._extract_dependencies_from_actions(actions)
                
                self.graph.add_scenario(
                    name=scenario_name,
                    dependencies=dependencies,
                    actions=actions,
                    glyph_file=f"{scenario_name}.glyph"
                )
                
                logger.debug(f"Added to graph: {scenario_name} with {len(dependencies)} dependencies")
                
            except Exception as e:
                logger.error(f"Failed to load guide {guide_file}: {e}")
        
        # Validate the graph
        is_valid, errors = self.graph.validate_graph()
        if not is_valid:
            logger.error("Graph validation failed:")
            for error in errors:
                logger.error(f"  {error}")
            raise ValueError("Invalid scenario graph")
        
        logger.info("✅ Scenario graph built successfully")
        self.graph.print_graph_info()
        
        return self.graph
    
    def _extract_dependencies_from_actions(self, actions: List[str]) -> List[str]:
        """Extract scenario dependencies from action list."""
        dependencies = []
        
        for action in actions:
            # Look for [ref: scenario_name] pattern
            if '[ref:' in action and ']' in action:
                start = action.find('[ref:') + 5
                end = action.find(']', start)
                if start > 4 and end > start:
                    scenario_name = action[start:end].strip()
                    if scenario_name not in dependencies:
                        dependencies.append(scenario_name)
        
        return dependencies
