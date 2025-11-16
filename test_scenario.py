import json
from core.config import Config
from core.llm import OpenAILLM
from core.template_manager import TemplateManager
from core.pipeline import PipelineContext
from core.stages import LoadStage, SortStage, ValidateStage


config = Config()
llm = OpenAILLM(model=config.llm_model)
template_manager = TemplateManager()

context = PipelineContext(config=config, llm=llm, template_manager=template_manager)

load_stage = LoadStage('load_scenarios')
sort_stage = SortStage('sort_scenarios')
validate_stage = ValidateStage('validate_scenarios')
load_stage.set_next(sort_stage)
sort_stage.set_next(validate_stage)

load_stage.execute(context)

print('\nDependencies:')
for scenario_name, dependencies in context.scenario_links.items():
    if dependencies:
        print(f'\n{scenario_name} depends on:')
        for dep in dependencies:
            if isinstance(dep, dict) and 'scenario' in dep:
                print(f'  - {dep["scenario"]}: {dep.get("justification", "No justification")}')
            else:
                print(f'  - {dep}')
    else:
        print(f'{scenario_name} has no dependencies')

print('\nTopological Sort Order:')
if hasattr(context, 'sorted_scenarios'):
    for i, scenario_name in enumerate(context.sorted_scenarios, 1):
        print(f'  {i}. {scenario_name}')
else:
    print('  No sorted order available')
