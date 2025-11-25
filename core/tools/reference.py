import json
import re
from pathlib import Path
from core.config import Config
from core.template_manager import TemplateManager
from core.llm import LangChainLLM
from core.scenario import Scenario
from core.build_progress import BuildProgress, ScenarioProgress
from core.playwright_env import ensure_playwright_environment


def check_scenario_reference(scenario_a: Scenario, scenario_b: Scenario, llm: LangChainLLM = None) -> dict:
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    system_prompt = template_manager.check_scenario_reference_system_prompt()
    user_prompt = template_manager.check_scenario_reference_user_prompt(scenario_a, scenario_b)
    
    response = llm.process(user_prompt, system_prompt=system_prompt)
    response = response.strip()
    
    code_block_pattern = r'```(?:json)?\n?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        response = match.group(1).strip()
    
    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'Failed to parse LLM response as JSON',
            'raw_response': response[:500],
            'references': False
        }


def find_all_references(scenarios: list[Scenario], llm: LangChainLLM = None, verbose: bool = False) -> dict:
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    references_map = {}
    total_pairs = len(scenarios) * (len(scenarios) - 1)
    current = 0
    
    for scenario_a in scenarios:
        references_map[scenario_a.name] = []
        
        for scenario_b in scenarios:
            if scenario_a.name == scenario_b.name:
                continue
            
            current += 1
            if verbose:
                print(f'[{current}/{total_pairs}] Checking if {scenario_a.name} references {scenario_b.name}...')
            
            result = check_scenario_reference(scenario_a, scenario_b, llm)
            
            if result.get('references', False):
                references_map[scenario_a.name].append(scenario_b.name)
                if verbose:
                    justification = result.get('justification', '')[:100]
                    print(f'  ✓ {scenario_a.name} references {scenario_b.name}: {justification}...')
    
    return references_map


def find_all_references_and_update_progress(verbose: str = 'false') -> str:
    verbose_bool = verbose.lower() == 'true' if isinstance(verbose, str) else bool(verbose)
    config = Config()
    llm = LangChainLLM(model=config.llm_model)
    
    scenarios_dir = Path(config.scenarios_dir)
    if not scenarios_dir.exists():
        return json.dumps({
            'success': False,
            'error': f'Scenarios directory not found: {scenarios_dir}'
        })
    
    scenario_files = list(scenarios_dir.glob('*.glyph'))
    scenarios = []
    
    for scenario_file in scenario_files:
        scenario_text = scenario_file.read_text()
        scenario = Scenario(scenario_text, name=scenario_file.name)
        scenarios.append(scenario)
    
    if verbose_bool:
        print(f'Found {len(scenarios)} scenarios')
        print('Analyzing references...\n')
    
    references_map = find_all_references(scenarios, llm, verbose_bool)
    
    glyph_dir = ensure_playwright_environment()
    progress_path = glyph_dir / 'build_progress.json'
    progress = BuildProgress.load(progress_path)
    
    for scenario_name, references in references_map.items():
        if scenario_name not in progress.scenarios:
            progress.scenarios[scenario_name] = ScenarioProgress(
                scenario_name=scenario_name,
                scenario_path=str(scenarios_dir / scenario_name),
                status='not_yet_implemented',
                dependencies=[],
                references=references
            )
        else:
            progress.scenarios[scenario_name].references = references
    
    progress.save(progress_path)
    
    return json.dumps({
        'success': True,
        'references': references_map,
        'total_scenarios': len(scenarios),
        'total_references': sum(len(refs) for refs in references_map.values())
    })


def check_scenario_reference_tool(scenario_a_name: str, scenario_b_name: str) -> str:
    config = Config()
    scenarios_dir = Path(config.scenarios_dir)
    
    scenario_a_path = scenarios_dir / scenario_a_name
    scenario_b_path = scenarios_dir / scenario_b_name
    
    if not scenario_a_path.exists():
        return json.dumps({
            'success': False,
            'error': f'Scenario A not found: {scenario_a_name}'
        })
    
    if not scenario_b_path.exists():
        return json.dumps({
            'success': False,
            'error': f'Scenario B not found: {scenario_b_name}'
        })
    
    scenario_a_text = scenario_a_path.read_text()
    scenario_b_text = scenario_b_path.read_text()
    
    scenario_a = Scenario(scenario_a_text, name=scenario_a_name)
    scenario_b = Scenario(scenario_b_text, name=scenario_b_name)
    
    result = check_scenario_reference(scenario_a, scenario_b)
    
    return json.dumps({
        'success': True,
        'scenario_a': scenario_a_name,
        'scenario_b': scenario_b_name,
        **result
    })

