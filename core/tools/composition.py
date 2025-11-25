import json
import re
from core.config import Config
from core.template_manager import TemplateManager
from core.llm import LangChainLLM


def compose_spec_with_base(base_code: str, additional_code: str, llm: LangChainLLM = None) -> str:
    if not additional_code.strip():
        return base_code
    
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    system_prompt = template_manager.compose_spec_system_prompt()
    user_prompt = template_manager.compose_spec_user_prompt(base_code, additional_code)
    
    response = llm.process(user_prompt, system_prompt=system_prompt)
    
    response = response.strip()
    
    code_block_pattern = r'```(?:javascript|js)?\n?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        response = match.group(1).strip()
    
    return response


def compose_spec(base_url: str, additional_code: str, llm: LangChainLLM = None, base_code: str = None) -> str:
    template_manager = TemplateManager()
    
    if base_code is None:
        base_code = template_manager.step0_playwright_template(base_url=base_url)
    
    return compose_spec_with_base(base_code, additional_code, llm)


def compose_spec_tool(base_url: str, additional_code: str) -> str:
    return compose_spec(base_url, additional_code)

