import sys
import argparse
from pathlib import Path
from core.config import Config
from core.llm import LangChainLLM
from core.template_manager import TemplateManager
from core.pipeline import PipelineContext
from core.stages import LoadStage
from core.build_agent import BuildAgent


class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='glyph', description='GlyphQA test generation system')
        self.subparsers = self.parser.add_subparsers(dest='command', help='Available commands')
        
        self._setup_build_command()
    
    def _setup_build_command(self):
        build_parser = self.subparsers.add_parser('build', help='Build test scenarios')
        build_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed build progress')
    
    def run(self, args=None):
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            sys.exit(1)
        
        if parsed_args.command == 'build':
            self._handle_build(parsed_args)
        else:
            self.parser.print_help()
            sys.exit(1)
    
    def _handle_build(self, args):
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
        template_manager = TemplateManager()
        
        context = PipelineContext(config=config, llm=llm, template_manager=template_manager)
        
        load_stage = LoadStage('load_scenarios')
        scenarios = load_stage.execute(context)
        
        agent = BuildAgent(config, llm, template_manager, verbose=args.verbose)
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
