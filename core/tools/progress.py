import json
from pathlib import Path
from core.build_progress import BuildProgress
from core.playwright_env import ensure_playwright_environment


def read_build_progress() -> str:
    glyph_dir = ensure_playwright_environment()
    progress_path = glyph_dir / 'build_progress.json'
    
    progress = BuildProgress.load(progress_path)
    
    scenarios_data = {
        name: {
            'scenario_name': prog.scenario_name,
            'scenario_path': prog.scenario_path,
            'status': prog.status,
            'dependencies': prog.dependencies,
            'references': getattr(prog, 'references', []),
            'current_reference_building': prog.current_reference_building,
            'error_message': prog.error_message,
            'spec_file_path': prog.spec_file_path,
        }
        for name, prog in progress.scenarios.items()
    }
    
    return json.dumps({
        'success': True,
        'current_scenario': progress.current_scenario,
        'scenarios': scenarios_data,
        'not_yet_implemented': progress.get_not_yet_implemented(),
        'in_progress': progress.get_in_progress(),
        'completed': progress.get_completed(),
        'failed': progress.get_failed(),
    })


def get_scenario_status(scenario_name: str) -> str:
    glyph_dir = ensure_playwright_environment()
    progress_path = glyph_dir / 'build_progress.json'
    
    progress = BuildProgress.load(progress_path)
    
    if scenario_name not in progress.scenarios:
        return json.dumps({
            'success': False,
            'error': f'Scenario not found: {scenario_name}'
        })
    
    prog = progress.scenarios[scenario_name]
    
    return json.dumps({
        'success': True,
        'scenario_name': prog.scenario_name,
        'scenario_path': prog.scenario_path,
        'status': prog.status,
        'dependencies': prog.dependencies,
        'references': getattr(prog, 'references', []),
        'current_reference_building': prog.current_reference_building,
        'error_message': prog.error_message,
        'spec_file_path': prog.spec_file_path,
        'has_spec_code': prog.current_spec_code is not None,
    })


def get_not_yet_implemented_scenarios() -> str:
    glyph_dir = ensure_playwright_environment()
    progress_path = glyph_dir / 'build_progress.json'
    
    progress = BuildProgress.load(progress_path)
    scenarios = progress.get_not_yet_implemented()
    
    return json.dumps({
        'success': True,
        'scenarios': scenarios,
        'count': len(scenarios)
    })


def update_scenario_status(scenario_name: str, status: str, error_message: str = None, spec_file_path: str = None) -> str:
    glyph_dir = ensure_playwright_environment()
    progress_path = glyph_dir / 'build_progress.json'
    
    progress = BuildProgress.load(progress_path)
    
    if scenario_name not in progress.scenarios:
        return json.dumps({
            'success': False,
            'error': f'Scenario not found: {scenario_name}'
        })
    
    if status == 'in_progress':
        progress.mark_in_progress(scenario_name)
    elif status == 'completed':
        if not spec_file_path:
            return json.dumps({
                'success': False,
                'error': 'spec_file_path is required for completed status'
            })
        progress.mark_completed(scenario_name, spec_file_path)
    elif status == 'failed':
        error_msg = error_message or 'Unknown error'
        progress.mark_failed(scenario_name, error_msg)
    else:
        return json.dumps({
            'success': False,
            'error': f'Invalid status: {status}. Must be one of: in_progress, completed, failed'
        })
    
    progress.save(progress_path)
    
    return json.dumps({
        'success': True,
        'scenario_name': scenario_name,
        'status': status
    })


def read_build_progress_tool() -> str:
    return read_build_progress()


def get_scenario_status_tool(scenario_name: str) -> str:
    return get_scenario_status(scenario_name)


def get_not_yet_implemented_scenarios_tool() -> str:
    return get_not_yet_implemented_scenarios()


def update_scenario_status_tool(scenario_name: str, status: str, error_message: str = None, spec_file_path: str = None) -> str:
    return update_scenario_status(scenario_name, status, error_message, spec_file_path)

