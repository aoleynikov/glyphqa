import json
import re
from core.config import Config
from core.template_manager import TemplateManager
from core.llm import LangChainLLM


def analyze_spec_implementation(spec_code: str, scenario_text: str, llm: LangChainLLM = None) -> str:
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    system_prompt = template_manager.analyze_spec_implementation_system_prompt()
    user_prompt = template_manager.analyze_spec_implementation_user_prompt(spec_code, scenario_text)
    
    response = llm.process(user_prompt, system_prompt=system_prompt)
    
    response = response.strip()
    
    code_block_pattern = r'```(?:json)?\n?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        response = match.group(1).strip()
    
    try:
        json.loads(response)
    except json.JSONDecodeError:
        pass
    
    return response


def analyze_spec_implementation_tool(spec_code: str, scenario_text: str) -> str:
    return analyze_spec_implementation(spec_code, scenario_text)


def validate_scenario_implementation(scenario_text: str, spec_code: str, llm: LangChainLLM = None) -> str:
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    system_prompt = template_manager.validate_scenario_implementation_system_prompt()
    user_prompt = template_manager.validate_scenario_implementation_user_prompt(scenario_text, spec_code)
    
    response = llm.process(user_prompt, system_prompt=system_prompt)
    response = response.strip()
    
    code_block_pattern = r'```(?:json)?\n?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        response = match.group(1).strip()
    
    try:
        json.loads(response)
    except json.JSONDecodeError:
        pass
    
    return response


def validate_scenario_implementation_tool(scenario_text: str, spec_code: str) -> str:
    return validate_scenario_implementation(scenario_text, spec_code)

