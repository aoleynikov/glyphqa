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
        self._setup_purge_command()
    
    def _setup_build_command(self):
        build_parser = self.subparsers.add_parser('build', help='Build test scenarios')
        build_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed build progress')
    
    def _setup_purge_command(self):
        purge_parser = self.subparsers.add_parser('purge', help='Clear all build agent persisted data')
        purge_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation prompt')
    
    def run(self, args=None):
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            sys.exit(1)
        
        if parsed_args.command == 'build':
            self._handle_build(parsed_args)
        elif parsed_args.command == 'purge':
            self._handle_purge(parsed_args)
        else:
            self.parser.print_help()
            sys.exit(1)
    
    def _handle_build(self, args):
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
        template_manager = TemplateManager()
        
        context = PipelineContext(config=config, llm=llm, template_manager=template_manager)
        
        load_stage = LoadStage('load_scenarios')
        load_stage.execute(context)
        
        scenarios = context.scenarios
        
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
    
    def _handle_purge(self, args):
        from core.playwright_env import ensure_playwright_environment
        
        config = Config()
        glyph_dir = ensure_playwright_environment(config.connection_url)
        
        files_to_remove = []
        files_to_remove.append(glyph_dir / 'build_progress.json')
        
        for spec_file in glyph_dir.glob('*.spec.js'):
            files_to_remove.append(spec_file)
        
        existing_files = [f for f in files_to_remove if f.exists()]
        
        if not existing_files:
            print('No build data to purge.')
            return
        
        if not args.force:
            print('The following files will be removed:')
            for f in existing_files:
                print(f'  - {f}')
            response = input('\nContinue? (y/N): ')
            if response.lower() != 'y':
                print('Purge cancelled.')
                return
        
        removed_count = 0
        for f in existing_files:
            try:
                f.unlink()
                removed_count += 1
            except Exception as e:
                print(f'Error removing {f}: {e}')
        
        print(f'\nPurged {removed_count} file(s).')
