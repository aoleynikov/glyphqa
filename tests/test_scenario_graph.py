#!/usr/bin/env python3

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from core.scenario_graph import ScenarioGraph, ScenarioNode, ScenarioGraphBuilder


class TestScenarioGraph:
    """Test scenario graph and topological sorting."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.guides_dir = Path(self.temp_dir) / ".glyph" / "guides"
        self.guides_dir.mkdir(parents=True)
        
        # Create test guide files
        self._create_test_guides()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_guides(self):
        """Create test guide files for testing."""
        guides = {
            "login_as_admin": {
                "name": "login_as_admin",
                "actions": ["navigate to login", "type admin", "type password", "submit"],
                "dependencies": []
            },
            "create_user": {
                "name": "create_user", 
                "actions": ["[ref: login_as_admin] login", "navigate to users", "create user"],
                "dependencies": ["login_as_admin"]
            },
            "delete_user": {
                "name": "delete_user",
                "actions": ["[ref: create_user] create user first", "navigate to users", "delete user"],
                "dependencies": ["create_user"]
            },
            "logout": {
                "name": "logout",
                "actions": ["click logout button"],
                "dependencies": []
            }
        }
        
        for name, data in guides.items():
            guide_file = self.guides_dir / f"{name}.guide"
            with open(guide_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def test_scenario_graph_creation(self):
        """Test creating a scenario graph."""
        graph = ScenarioGraph()
        
        # Add scenarios
        graph.add_scenario("login_as_admin", dependencies=[])
        graph.add_scenario("create_user", dependencies=["login_as_admin"])
        graph.add_scenario("delete_user", dependencies=["create_user"])
        
        assert len(graph.nodes) == 3
        assert "login_as_admin" in graph.nodes
        assert "create_user" in graph.nodes
        assert "delete_user" in graph.nodes
    
    def test_dependency_extraction(self):
        """Test extracting dependencies from actions."""
        builder = ScenarioGraphBuilder(self.guides_dir)
        
        actions = [
            "[ref: login_as_admin] login as admin",
            "navigate to users",
            "[ref: create_user] create user",
            "verify user exists"
        ]
        
        dependencies = builder._extract_dependencies_from_actions(actions)
        assert "login_as_admin" in dependencies
        assert "create_user" in dependencies
        assert len(dependencies) == 2
    
    def test_graph_building_from_guides(self):
        """Test building graph from guide files."""
        builder = ScenarioGraphBuilder(self.guides_dir)
        graph = builder.build_graph_from_guides()
        
        assert len(graph.nodes) == 4
        
        # Check dependencies
        assert graph.get_dependencies_for_scenario("login_as_admin") == []
        assert graph.get_dependencies_for_scenario("create_user") == ["login_as_admin"]
        assert graph.get_dependencies_for_scenario("delete_user") == ["create_user"]
        assert graph.get_dependencies_for_scenario("logout") == []
    
    def test_topological_sort(self):
        """Test topological sorting."""
        graph = ScenarioGraph()
        
        # Create a simple dependency chain
        graph.add_scenario("A", dependencies=[])
        graph.add_scenario("B", dependencies=["A"])
        graph.add_scenario("C", dependencies=["B"])
        
        sorted_order = graph.topological_sort()
        
        # Should be A -> B -> C
        assert sorted_order == ["A", "B", "C"]
    
    def test_build_layers(self):
        """Test getting build layers."""
        graph = ScenarioGraph()
        
        # Create scenarios with dependencies
        graph.add_scenario("login", dependencies=[])
        graph.add_scenario("create_user", dependencies=["login"])
        graph.add_scenario("delete_user", dependencies=["create_user"])
        graph.add_scenario("logout", dependencies=[])
        
        layers = graph.get_build_layers()
        
        # Should have 3 layers:
        # Layer 1: login, logout (no dependencies)
        # Layer 2: create_user (depends on login)
        # Layer 3: delete_user (depends on create_user)
        assert len(layers) == 3
        assert set(layers[0]) == {"login", "logout"}
        assert layers[1] == ["create_user"]
        assert layers[2] == ["delete_user"]
    
    def test_cycle_detection(self):
        """Test detecting circular dependencies."""
        graph = ScenarioGraph()
        
        # Create a cycle: A -> B -> C -> A
        graph.add_scenario("A", dependencies=["C"])
        graph.add_scenario("B", dependencies=["A"])
        graph.add_scenario("C", dependencies=["B"])
        
        is_valid, errors = graph.validate_graph()
        assert not is_valid
        assert len(errors) > 0
        assert "Circular dependency" in errors[0]
    
    def test_missing_dependency_detection(self):
        """Test detecting missing dependencies."""
        graph = ScenarioGraph()
        
        # Create scenario with missing dependency
        graph.add_scenario("A", dependencies=["missing_scenario"])
        
        is_valid, errors = graph.validate_graph()
        assert not is_valid
        assert len(errors) > 0
        assert "missing scenario" in errors[0]
    
    def test_scenario_building_tracking(self):
        """Test tracking which scenarios have been built."""
        graph = ScenarioGraph()
        
        graph.add_scenario("A", dependencies=[])
        graph.add_scenario("B", dependencies=["A"])
        
        # Initially, no scenarios are built
        assert not graph.nodes["A"].built
        assert not graph.nodes["B"].built
        
        # Mark A as built
        graph.mark_scenario_built("A")
        assert graph.nodes["A"].built
        assert not graph.nodes["B"].built
        
        # Check unbuilt dependencies
        assert graph.get_unbuilt_dependencies("A") == []
        assert graph.get_unbuilt_dependencies("B") == []
    
    def test_dependents_tracking(self):
        """Test tracking which scenarios depend on a given scenario."""
        graph = ScenarioGraph()
        
        graph.add_scenario("A", dependencies=[])
        graph.add_scenario("B", dependencies=["A"])
        graph.add_scenario("C", dependencies=["A"])
        
        dependents = graph.get_dependents_of_scenario("A")
        assert set(dependents) == {"B", "C"}
        
        dependents = graph.get_dependents_of_scenario("B")
        assert dependents == []
    
    def test_complex_dependency_graph(self):
        """Test a more complex dependency graph."""
        graph = ScenarioGraph()
        
        # Create a complex graph:
        # login -> create_user -> delete_user
        # login -> logout
        # create_user -> verify_user
        graph.add_scenario("login", dependencies=[])
        graph.add_scenario("logout", dependencies=["login"])
        graph.add_scenario("create_user", dependencies=["login"])
        graph.add_scenario("delete_user", dependencies=["create_user"])
        graph.add_scenario("verify_user", dependencies=["create_user"])
        
        layers = graph.get_build_layers()
        
        # Should have 4 layers:
        # Layer 1: login
        # Layer 2: logout, create_user
        # Layer 3: delete_user, verify_user
        assert len(layers) == 3
        assert layers[0] == ["login"]
        assert set(layers[1]) == {"logout", "create_user"}
        assert set(layers[2]) == {"delete_user", "verify_user"}
        
        # Test topological sort
        sorted_order = graph.topological_sort()
        assert "login" in sorted_order[:1]  # login should be first
        assert "delete_user" in sorted_order[-2:]  # delete_user should be near the end
    
    def test_graph_visualization(self):
        """Test graph visualization functionality."""
        graph = ScenarioGraph()
        
        # Create a simple graph
        graph.add_scenario("A", dependencies=[])
        graph.add_scenario("B", dependencies=["A"])
        graph.add_scenario("C", dependencies=["A", "B"])
        
        # Test full graph visualization
        viz = graph.visualize_graph()
        assert "📊 Scenario Dependency Graph" in viz
        assert "Layer 1:" in viz
        assert "Layer 2:" in viz
        assert "A → B" in viz
        assert "B → C" in viz
        
        # Test scenario-specific visualization
        viz = graph.visualize_graph("C")
        assert "Focus: C" in viz
        assert "Dependencies (required):" in viz
        assert "A" in viz
        assert "B" in viz
        assert "TARGET" in viz
    
    def test_dependency_tree_visualization(self):
        """Test dependency tree visualization."""
        graph = ScenarioGraph()
        
        # Create a tree structure
        graph.add_scenario("root", dependencies=[])
        graph.add_scenario("child1", dependencies=["root"])
        graph.add_scenario("child2", dependencies=["root"])
        graph.add_scenario("grandchild", dependencies=["child1"])
        
        tree = graph.visualize_dependency_tree("grandchild")
        assert "🌳 Dependency Tree for: grandchild" in tree
        assert "root" in tree
        assert "child1" in tree
        assert "grandchild" in tree


if __name__ == "__main__":
    pytest.main([__file__])
