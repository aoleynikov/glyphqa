import sys
from core.config import Config
from core.llm import LangChainLLM
from core.template_manager import TemplateManager
from core.pipeline import PipelineContext
from core.stages import LoadStage
from core.build_agent import BuildAgent

config = Config()
llm = LangChainLLM(model=config.llm_model)
template_manager = TemplateManager()

context = PipelineContext(config=config, llm=llm, template_manager=template_manager)

load_stage = LoadStage('load_scenarios')
load_stage.execute(context)

scenarios = context.scenarios

verbose = '-v' in sys.argv or '--verbose' in sys.argv
if __name__ == '__main__':
    agent = BuildAgent(config, llm, template_manager, verbose=verbose)
    progress = agent.build_all_scenarios(scenarios)

    report = progress.get_final_report()

    print('\nBuild Report:')
    print('=' * 60)
    for scenario_path, status in sorted(report.items()):
        status_symbol = '✓' if status == 'completed' else '✗' if status == 'failed' else '○'
        print(f'{status_symbol} {scenario_path}: {status}')
    print('=' * 60)

    completed = len(progress.get_completed())
    failed = len(progress.get_failed())
    total = len(progress.scenarios)

    print(f'\nSummary: {completed}/{total} completed, {failed} failed')
