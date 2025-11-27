import json
import re
from pathlib import Path
from core.build_progress import BuildProgress, ScenarioProgress
from core.config import Config
from core.llm import LangChainLLM
from core.template_manager import TemplateManager
from core.scenario import Scenario
from core.tools import (
    compose_spec_with_base,
    run_steps_with_page_state,
)
from core.tools.generation import build_next_step
from core.playwright_env import ensure_playwright_environment


def _filter_page_state_output(output: str) -> str:
    if not output:
        return ''
    
    json_pattern = r'(?:Page State|Interactive Elements|Additional Page State|Final Page State)[:\s]*\n?(\{.*?\})'
    matches = re.findall(json_pattern, output, re.DOTALL)
    
    if matches:
        return '\n\n'.join(matches)
    
    lines = output.split('\n')
    filtered_lines = []
    skip_line = False
    
    for line in lines:
        stripped = line.strip().lower()
        
        if any(error_keyword in stripped for error_keyword in [
            'playwright requires', 'node.js', 'error:', 'warning:', 'exception'
        ]):
            skip_line = True
            continue
        
        if skip_line and (stripped == '' or not stripped.startswith('at ')):
            skip_line = False
        
        if skip_line:
            continue
        
        if stripped and not any(prefix in stripped for prefix in [
            'running', 'test outcome', 'failed', 'passed'
        ]):
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()


class BuildAgent:
    def __init__(self, config: Config, llm: LangChainLLM, template_manager: TemplateManager, verbose: bool = False):
        self.config = config
        self.llm = llm
        self.template_manager = template_manager
        self.verbose = verbose
        self.glyph_dir = ensure_playwright_environment(config.connection_url)
        self.progress_path = self.glyph_dir / 'build_progress.json'
        self._indent_level = 0
    
    def _log(self, message: str, level: str = 'info', data: dict = None):
        indent = '  ' * self._indent_level
        prefix = {
            'info': '→',
            'debug': '  ',
            'success': '✓',
            'error': '✗',
            'warning': '⚠',
        }.get(level, '→')
        
        print(f'{indent}{prefix} {message}', flush=True)
        
        if data and self.verbose:
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + '...'
                print(f'{indent}    {key}: {value}', flush=True)
    
    def _push_indent(self):
        self._indent_level += 1
    
    def _pop_indent(self):
        self._indent_level = max(0, self._indent_level - 1)

    def build_all_scenarios(self, scenarios: list[Scenario]) -> BuildProgress:
        self._log(f'Starting build process for {len(scenarios)} scenario(s)')
        
        progress = BuildProgress.load(self.progress_path)
        
        scenario_dict = {scenario.name: scenario for scenario in scenarios}
        
        for scenario in scenarios:
            if scenario.name not in progress.scenarios:
                progress.scenarios[scenario.name] = ScenarioProgress(
                    scenario_name=scenario.name,
                    scenario_path=str(Path(self.config.scenarios_dir) / scenario.name),
                    status='not_yet_implemented',
                    dependencies=[]
                )
        
        progress.save(self.progress_path)
        
        total = len(progress.get_not_yet_implemented())
        completed_count = 0
        
        while progress.get_not_yet_implemented():
            remaining = len(progress.get_not_yet_implemented())
            scenario_name = progress.get_not_yet_implemented()[0]
            scenario = scenario_dict[scenario_name]
            
            self._log(f'[{completed_count + 1}/{total}] Building: {scenario_name}')
            self._push_indent()
            
            success = self.build_scenario(scenario, progress, scenario_dict)
            progress.save(self.progress_path)
            
            self._pop_indent()
            
            if success:
                completed_count += 1
                self._log(f'Completed: {scenario_name}', 'success')
            else:
                self._log(f'Failed: {scenario_name}', 'error')
            
            print()
        
        return progress

    def build_scenario(self, scenario: Scenario, progress: BuildProgress, scenario_dict: dict[str, Scenario]) -> bool:
        progress.mark_in_progress(scenario.name)
        progress.save(self.progress_path)
        
        self._log('Starting iterative build...')
        self._push_indent()
        success = self.iterative_build(scenario, progress, scenario_dict)
        self._pop_indent()
        
        if success:
            scenario_progress = progress.scenarios[scenario.name]
            glyph_dir = ensure_playwright_environment(self.config.connection_url)
            spec_filename = Path(scenario.name).stem + '.spec.js'
            spec_path = glyph_dir / spec_filename
            
            if not spec_path.exists():
                if scenario_progress.current_spec_code:
                    spec_path.write_text(scenario_progress.current_spec_code)
                    if not spec_path.exists():
                        progress.mark_failed(scenario.name, f'Failed to create spec file at {spec_path}')
                        return False
                else:
                    progress.mark_failed(scenario.name, f'Spec file does not exist and current_spec_code is empty')
                    return False
            
            progress.mark_completed(scenario.name, str(spec_path))
            self._log(f'Saved spec to: {spec_path}', 'success')
        else:
            progress.mark_failed(scenario.name, 'Iterative build did not complete successfully')
        
        return success

    def iterative_build(self, scenario: Scenario, progress: BuildProgress, scenario_dict: dict[str, Scenario]) -> bool:
        scenario_progress = progress.scenarios[scenario.name]
        
        if not scenario_progress.step_list:
            self._log('Converting scenario to steps...')
            step_list = scenario.to_steps(self.llm, self.template_manager)
            scenario_progress.step_list = step_list
            progress.save(self.progress_path)
            self._log(f'Found {len(step_list)} steps')
        else:
            step_list = scenario_progress.step_list
        
        if not step_list:
            self._log('No steps found in scenario', 'error')
            return False
        
        current_spec = scenario_progress.current_spec_code
        if current_spec is None:
            self._log('Initializing with step0 template')
            current_spec = self.template_manager.step0_playwright_template(
                base_url=self.config.connection_url
            )
            progress.update_spec_code(scenario.name, current_spec)
        
        completed_steps = scenario_progress.completed_steps or []
        total_steps = len(step_list)
        
        all_scenarios_list = [
            {'path': s.name, 'text': s.text}
            for s in scenario_dict.values()
        ]
        all_scenarios_text = self.template_manager.list_scenarios(all_scenarios_list)
        
        while len(completed_steps) < total_steps:
            current_step_index = len(completed_steps)
            step_description = step_list[current_step_index] if current_step_index < len(step_list) else 'Unknown step'
            self._log(f'Building step {current_step_index + 1}/{total_steps}: {step_description}')
            self._push_indent()
            
            self._log('Running test to capture page state...')
            result_json = run_steps_with_page_state(
                code_lines='',
                base_url=self.config.connection_url,
                llm=self.llm,
                existing_spec=current_spec
            )
            
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError:
                self._log('Failed to parse test result', 'error')
                self._pop_indent()
                return False
            
            outcome = result.get('outcome', 'unknown')
            duration = result.get('duration', 0)
            outcome_msg = f'Test outcome: {outcome} ({duration:.2f}s)'
            if outcome == 'failed' and current_step_index == 0:
                outcome_msg += ' (expected - spec is incomplete during incremental build)'
            self._log(outcome_msg)
            
            if outcome == 'error':
                self._log('Test execution error', 'error')
                if self.verbose and result.get('output'):
                    output = result.get('output', '')[:500]
                    self._log(f'Error output: {output}', 'debug')
                self._pop_indent()
                return False
            
            current_spec = result.get('spec_code', current_spec)
            raw_output = result.get('output', '')
            page_state_output = _filter_page_state_output(raw_output)
            
            self._log('Building next step...')
            build_result_json = build_next_step(
                all_scenarios=all_scenarios_text,
                current_scenario_name=scenario.name,
                current_scenario_path=scenario_progress.scenario_path,
                current_scenario_text=scenario.text,
                step_list=step_list,
                completed_steps_indices=completed_steps,
                current_spec=current_spec,
                page_state_output=page_state_output,
                llm=self.llm
            )
            
            try:
                build_result = json.loads(build_result_json)
            except json.JSONDecodeError:
                self._log('Failed to parse build result', 'error')
                self._pop_indent()
                return False
            
            if not build_result.get('success'):
                self._log('Build step failed', 'error')
                self._pop_indent()
                return False
            
            updated_spec = build_result.get('spec_code', current_spec)
            if updated_spec:
                current_spec = updated_spec
                progress.update_spec_code(scenario.name, current_spec)
                completed_steps.append(current_step_index)
                scenario_progress.completed_steps = completed_steps
                progress.save(self.progress_path)
                self._log('Step completed', 'success')
            else:
                self._log('No spec code generated', 'warning')
                self._pop_indent()
                return False
            
            self._pop_indent()
        
        self._log('All steps completed', 'success')
        
        scenario_progress = progress.scenarios[scenario.name]
        glyph_dir = ensure_playwright_environment(self.config.connection_url)
        spec_filename = Path(scenario.name).stem + '.spec.js'
        spec_path = glyph_dir / spec_filename
        spec_path.write_text(current_spec)
        progress.update_spec_code(scenario.name, current_spec)
        
        if not spec_path.exists():
            self._log(f'Warning: Spec file was not created at {spec_path}', 'warning')
            return False
        
        return True

