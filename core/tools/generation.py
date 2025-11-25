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

