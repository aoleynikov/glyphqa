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
    analyze_spec_implementation,
)
from core.playwright_env import ensure_playwright_environment


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
        
        print(f'{indent}{prefix} {message}')
        
        if data and self.verbose:
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 200:
                    value = value[:200] + '...'
                print(f'{indent}    {key}: {value}')
    
    def _push_indent(self):
        self._indent_level += 1
    
    def _pop_indent(self):
        self._indent_level = max(0, self._indent_level - 1)

    def build_all_scenarios(self, scenarios: list[Scenario]) -> BuildProgress:
        self._log(f'Starting build process for {len(scenarios)} scenario(s)')
        
        progress = BuildProgress.load(self.progress_path)
        
        scenario_dict = {scenario.name: scenario for scenario in scenarios}
        
        self._log('Analyzing scenario dependencies...')
        scenario_summaries = {
            s.name: s.summarize(self.llm, self.template_manager)
            for s in scenarios
        }
        
        for scenario in scenarios:
            if scenario.name not in progress.scenarios:
                dependencies = self._find_dependencies(scenario, scenario_summaries)
                
                progress.scenarios[scenario.name] = ScenarioProgress(
                    scenario_name=scenario.name,
                    scenario_path=str(Path(self.config.scenarios_dir) / scenario.name),
                    status='not_yet_implemented',
                    dependencies=dependencies
                )
                
                if dependencies:
                    self._log(f'{scenario.name} depends on: {", ".join(dependencies)}', 'debug')
        
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
        
        scenario_progress = progress.scenarios[scenario.name]
        if scenario_progress.dependencies:
            self._log(f'Resolving {len(scenario_progress.dependencies)} dependency(ies)...')
            self._push_indent()
        
        if not self.resolve_dependencies(scenario, progress, scenario_dict):
            if scenario_progress.dependencies:
                self._pop_indent()
            progress.mark_failed(scenario.name, 'Dependencies could not be resolved')
            return False
        
        if scenario_progress.dependencies:
            self._pop_indent()
        
        self._log('Starting iterative build...')
        self._push_indent()
        success = self.iterative_build(scenario, progress)
        self._pop_indent()
        
        if success:
            scenario_progress = progress.scenarios[scenario.name]
            spec_path = Path(scenario_progress.scenario_path).with_suffix('.spec.js')
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_path.write_text(scenario_progress.current_spec_code)
            progress.mark_completed(scenario.name, str(spec_path))
            self._log(f'Saved spec to: {spec_path}', 'success')
        else:
            progress.mark_failed(scenario.name, 'Iterative build did not complete successfully')
        
        return success

    def resolve_dependencies(self, scenario: Scenario, progress: BuildProgress, scenario_dict: dict[str, Scenario]) -> bool:
        scenario_progress = progress.scenarios[scenario.name]
        
        for dep_name in scenario_progress.dependencies:
            dep_progress = progress.scenarios.get(dep_name)
            
            if not dep_progress:
                continue
            
            if dep_progress.status == 'completed':
                self._log(f'Dependency already built: {dep_name}', 'debug')
                continue
            
            if dep_progress.status == 'failed':
                self._log(f'Dependency failed: {dep_name}', 'error')
                return False
            
            if dep_progress.status == 'in_progress':
                self._log(f'Dependency in progress: {dep_name}', 'warning')
                continue
            
            self._log(f'Building dependency: {dep_name}')
            progress.set_current_reference(scenario.name, dep_name)
            progress.save(self.progress_path)
            
            dep_scenario = scenario_dict.get(dep_name)
            if not dep_scenario:
                self._log(f'Dependency scenario not found: {dep_name}', 'error')
                return False
            
            self._push_indent()
            if not self.build_scenario(dep_scenario, progress, scenario_dict):
                self._pop_indent()
                return False
            self._pop_indent()
            
            progress.clear_current_reference(scenario.name)
            progress.save(self.progress_path)
            self._log(f'Dependency completed: {dep_name}', 'success')
        
        return True

    def iterative_build(self, scenario: Scenario, progress: BuildProgress) -> bool:
        scenario_progress = progress.scenarios[scenario.name]
        current_spec = None
        max_iterations = 20
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            self._log(f'Iteration {iteration}/{max_iterations}')
            self._push_indent()
            
            if current_spec is None:
                self._log('Initializing with step0 template')
                current_spec = self.template_manager.step0_playwright_template(
                    base_url=self.config.connection_url
                )
            
            self._log('Analyzing implementation progress...')
            analysis_json = analyze_spec_implementation(
                current_spec,
                scenario.text,
                self.llm
            )
            
            try:
                analysis = json.loads(analysis_json)
            except json.JSONDecodeError:
                analysis = {'implementation_status': 'unknown'}
            
            status = analysis.get('implementation_status', 'unknown')
            self._log(f'Status: {status}')
            
            if self.verbose:
                completed = analysis.get('completed_steps', [])
                missing = analysis.get('missing_steps', [])
                if completed:
                    self._log(f'Completed steps: {len(completed)}', 'debug')
                if missing:
                    self._log(f'Missing steps: {len(missing)}', 'debug')
            
            if status in ['complete', 'mostly complete']:
                self._log('Implementation complete!', 'success')
                scenario_progress = progress.scenarios[scenario.name]
                spec_path = Path(scenario_progress.scenario_path).with_suffix('.spec.js')
                spec_path.parent.mkdir(parents=True, exist_ok=True)
                spec_path.write_text(current_spec)
                progress.update_spec_code(scenario.name, current_spec)
                self._pop_indent()
                return True
            
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
            self._log(f'Test outcome: {outcome} ({duration:.2f}s)')
            
            if outcome == 'error':
                self._log('Test execution error', 'error')
                if self.verbose and result.get('output'):
                    output = result.get('output', '')[:500]
                    self._log(f'Error output: {output}', 'debug')
                self._pop_indent()
                return False
            
            current_spec = result.get('spec_code', current_spec)
            progress.update_spec_code(scenario.name, current_spec)
            
            next_steps = analysis.get('next_steps', [])
            if not next_steps:
                self._log('No next steps guidance available', 'warning')
                self._pop_indent()
                break
            
            next_step_guidance = next_steps[0]
            self._log(f'Next step: {next_step_guidance[:100]}...')
            
            self._log('Generating code...')
            page_state_output = result.get('output', '')
            
            system_prompt = self.template_manager.generate_next_code_system_prompt()
            user_prompt = self.template_manager.generate_next_code_user_prompt(
                page_state_output,
                next_step_guidance
            )
            
            next_code_response = self.llm.process(user_prompt, system_prompt=system_prompt)
            next_code_response = next_code_response.strip()
            
            code_block_pattern = r'```(?:javascript|js)?\n?(.*?)```'
            match = re.search(code_block_pattern, next_code_response, re.DOTALL)
            if match:
                next_code = match.group(1).strip()
            else:
                next_code = next_code_response
            
            if next_code:
                if self.verbose:
                    code_preview = next_code[:150] + '...' if len(next_code) > 150 else next_code
                    self._log(f'Generated code: {code_preview}', 'debug')
                
                current_spec = compose_spec_with_base(
                    current_spec,
                    next_code,
                    self.llm
                )
                progress.update_spec_code(scenario.name, current_spec)
                self._log('Code composed into spec')
            else:
                self._log('No code generated', 'warning')
            
            self._pop_indent()
        
        self._log(f'Reached max iterations ({max_iterations})', 'warning')
        return False

    def _find_dependencies(self, scenario: Scenario, scenario_summaries: dict[str, str]) -> list[str]:
        if self.verbose:
            self._log(f'Finding dependencies for: {scenario.name}', 'debug')
        
        prompt = self.template_manager.find_scenario_references(scenario, scenario_summaries)
        response = self.llm.process(prompt)
        
        try:
            dependencies = json.loads(response)
            deps = [dep['scenario'] for dep in dependencies if isinstance(dep, dict) and 'scenario' in dep]
            return deps
        except json.JSONDecodeError:
            return []

