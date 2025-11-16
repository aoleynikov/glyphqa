import json
from pathlib import Path
from core.pipeline import PipelineStage
from core.scenario import Scenario


class LoadStage(PipelineStage):
    def process(self, context):
        scenarios_dir = Path(context.config.scenarios_dir)
        if not scenarios_dir.exists():
            raise FileNotFoundError(f'Scenarios directory not found: {scenarios_dir}')
        
        scenario_files = list(scenarios_dir.glob('*.glyph'))
        scenarios = []
        
        for scenario_file in scenario_files:
            scenario_text = scenario_file.read_text()
            scenario = Scenario(scenario_text, name=scenario_file.name)
            scenarios.append(scenario)
        
        context.scenarios = scenarios
        return scenarios


class SortStage(PipelineStage):
    def process(self, context):
        scenario_links = {}
        for scenario_b in context.scenarios:
            dependencies = []
            for scenario_a in context.scenarios:
                if scenario_a.name == scenario_b.name:
                    continue
                
                prompt = context.template_manager.is_scenario_required(scenario_a, scenario_b)
                response = context.llm.process(prompt)
                
                try:
                    result = json.loads(response)
                except json.JSONDecodeError as e:
                    print(f'ERROR parsing JSON for {scenario_b.name} -> {scenario_a.name}: {e}')
                    print(f'Response: {response}')
                    continue
                
                if result.get('required', False):
                    dependencies.append({
                        'scenario': scenario_a.name,
                        'justification': result.get('justification', '')
                    })
            
            scenario_links[scenario_b.name] = dependencies
        
        context.scenario_links = scenario_links
        return scenario_links


class ValidateStage(PipelineStage):
    def process(self, context):
        scenario_links = context.scenario_links
        
        dependency_graph = {}
        reverse_graph = {}
        all_scenarios = set()
        
        for scenario_name, dependencies in scenario_links.items():
            all_scenarios.add(scenario_name)
            dependency_graph[scenario_name] = []
            for dep in dependencies:
                dep_name = dep['scenario'] if isinstance(dep, dict) else dep
                dependency_graph[scenario_name].append(dep_name)
                all_scenarios.add(dep_name)
                
                if dep_name not in reverse_graph:
                    reverse_graph[dep_name] = []
                reverse_graph[dep_name].append(scenario_name)
        
        for scenario_name in all_scenarios:
            if scenario_name not in dependency_graph:
                dependency_graph[scenario_name] = []
            if scenario_name not in reverse_graph:
                reverse_graph[scenario_name] = []
        
        cycles = self._detect_cycles(dependency_graph)
        if cycles:
            cycle_str = ' -> '.join(cycles[0]) + f' -> {cycles[0][0]}'
            raise ValueError(f'Circular dependency detected: {cycle_str}')
        
        sorted_order = self._topological_sort(reverse_graph)
        context.sorted_scenarios = sorted_order
        return sorted_order
    
    def _detect_cycles(self, graph):
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            cycle_found = False
            for neighbor in graph.get(node, []):
                if dfs(neighbor, path):
                    cycle_found = True
                    break
            
            if not cycle_found:
                rec_stack.remove(node)
                path.pop()
            
            return cycle_found
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _topological_sort(self, graph):
        in_degree = {node: 0 for node in graph}
        
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
        
        queue = [node for node in graph if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(graph):
            raise ValueError('Graph has cycles, cannot perform topological sort')
        
        return result

