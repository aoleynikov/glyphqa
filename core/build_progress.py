import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ScenarioProgress:
    scenario_name: str
    scenario_path: str
    status: str
    dependencies: List[str]
    references: List[str] = None
    current_spec_code: Optional[str] = None
    current_reference_building: Optional[str] = None
    error_message: Optional[str] = None
    spec_file_path: Optional[str] = None
    completed_steps: List[int] = None
    step_list: List[str] = None
    
    def __post_init__(self):
        if self.references is None:
            self.references = []
        if self.completed_steps is None:
            self.completed_steps = []
        if self.step_list is None:
            self.step_list = []

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class BuildProgress:
    def __init__(self):
        self.scenarios: Dict[str, ScenarioProgress] = {}
        self.current_scenario: Optional[str] = None

    def get_not_yet_implemented(self) -> List[str]:
        return [
            name for name, progress in self.scenarios.items()
            if progress.status != 'completed' and progress.status != 'failed'
        ]

    def get_in_progress(self) -> List[str]:
        return [
            name for name, progress in self.scenarios.items()
            if progress.status == 'in_progress'
        ]

    def get_completed(self) -> List[str]:
        return [
            name for name, progress in self.scenarios.items()
            if progress.status == 'completed'
        ]

    def get_failed(self) -> List[str]:
        return [
            name for name, progress in self.scenarios.items()
            if progress.status == 'failed'
        ]

    def mark_in_progress(self, scenario_name: str):
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name].status = 'in_progress'
            self.current_scenario = scenario_name

    def mark_completed(self, scenario_name: str, spec_file_path: str):
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name].status = 'completed'
            self.scenarios[scenario_name].spec_file_path = spec_file_path
            self.scenarios[scenario_name].current_spec_code = None
            self.scenarios[scenario_name].current_reference_building = None
            if self.current_scenario == scenario_name:
                self.current_scenario = None

    def mark_failed(self, scenario_name: str, error_message: str):
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name].status = 'failed'
            self.scenarios[scenario_name].error_message = error_message
            if self.current_scenario == scenario_name:
                self.current_scenario = None

    def set_current_reference(self, scenario_name: str, reference_name: str):
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name].current_reference_building = reference_name

    def clear_current_reference(self, scenario_name: str):
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name].current_reference_building = None

    def update_spec_code(self, scenario_name: str, spec_code: str):
        if scenario_name in self.scenarios:
            self.scenarios[scenario_name].current_spec_code = spec_code

    def get_final_report(self) -> Dict[str, str]:
        return {
            progress.scenario_path: progress.status
            for progress in self.scenarios.values()
        }

    def save(self, path: Path):
        data = {
            'scenarios': {
                name: progress.to_dict()
                for name, progress in self.scenarios.items()
            },
            'current_scenario': self.current_scenario
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> 'BuildProgress':
        if not path.exists():
            return cls()
        
        data = json.loads(path.read_text())
        progress = cls()
        progress.scenarios = {
            name: ScenarioProgress.from_dict(progress_data)
            for name, progress_data in data.get('scenarios', {}).items()
        }
        progress.current_scenario = data.get('current_scenario')
        return progress

