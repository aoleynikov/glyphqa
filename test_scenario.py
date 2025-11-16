import json
from pathlib import Path
from core.scenario import Scenario
from core.llm import OpenAILLM
from core.template_manager import TemplateManager


scenario_path = Path('scenarios/login_as_user.glyph')
scenario_text = scenario_path.read_text()

scenario = Scenario(scenario_text)
llm = OpenAILLM(model='gpt-4o-mini')
template_manager = TemplateManager()

steps = scenario.to_steps(llm, template_manager)

print('Steps:')
for i, step in enumerate(steps, 1):
    print(f'{i}. {step}')

