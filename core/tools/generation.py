import json
import re
from core.config import Config
from core.template_manager import TemplateManager
from core.llm import LangChainLLM


def generate_next_code(page_state_output: str, next_step_guidance: str, llm: LangChainLLM = None) -> str:
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    system_prompt = template_manager.generate_next_code_system_prompt()
    user_prompt = template_manager.generate_next_code_user_prompt(
        page_state_output,
        next_step_guidance
    )
    
    response = llm.process(user_prompt, system_prompt=system_prompt)
    response = response.strip()
    
    code_block_pattern = r'```(?:javascript|js)?\n?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        code = response
    
    return json.dumps({
        'success': True,
        'code': code,
        'raw_response': response
    })


def generate_next_code_tool(page_state_output: str, next_step_guidance: str) -> str:
    return generate_next_code(page_state_output, next_step_guidance)


def build_next_step(all_scenarios: str, current_scenario_name: str, current_scenario_path: str, current_scenario_text: str, step_list: list, completed_steps_indices: list, current_spec: str, page_state_output: str, llm: LangChainLLM = None) -> str:
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    system_prompt = template_manager.build_next_step_system_prompt()
    user_prompt = template_manager.build_next_step_user_prompt(
        all_scenarios=all_scenarios,
        current_scenario_name=current_scenario_name,
        current_scenario_path=current_scenario_path,
        current_scenario_text=current_scenario_text,
        step_list=step_list,
        completed_steps_indices=completed_steps_indices,
        current_spec=current_spec,
        page_state_output=page_state_output
    )
    
    response = llm.process(user_prompt, system_prompt=system_prompt)
    response = response.strip()
    
    code_block_pattern = r'```(?:javascript|js)?\n?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        spec_code = match.group(1).strip()
    else:
        spec_code = response
    
    return json.dumps({
        'success': True,
        'spec_code': spec_code,
        'raw_response': response
    })


def build_next_step_tool(all_scenarios: str, current_scenario_name: str, current_scenario_path: str, current_scenario_text: str, step_list: str, completed_steps_indices: str, current_spec: str, page_state_output: str) -> str:
    import json
    step_list_parsed = json.loads(step_list) if isinstance(step_list, str) else step_list
    completed_steps_parsed = json.loads(completed_steps_indices) if isinstance(completed_steps_indices, str) else completed_steps_indices
    return build_next_step(all_scenarios, current_scenario_name, current_scenario_path, current_scenario_text, step_list_parsed, completed_steps_parsed, current_spec, page_state_output)

