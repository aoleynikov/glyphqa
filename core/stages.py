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
