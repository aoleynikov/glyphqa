import sys
import argparse
from pathlib import Path


class CLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='glyph', description='GlyphQA test generation system')
        self.subparsers = self.parser.add_subparsers(dest='command', help='Available commands')
        
        self._setup_build_command()
    
    def _setup_build_command(self):
        self.subparsers.add_parser('build', help='Build test scenarios')
    
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
        from core.config import Config
        from core.llm import OpenAILLM
        from core.template_manager import TemplateManager
        from core.scenario import Scenario
        
        config = Config()
        llm = OpenAILLM(model=config.llm_model)
        template_manager = TemplateManager()
        
        scenarios_dir = Path(config.scenarios_dir)
        if not scenarios_dir.exists():
            raise FileNotFoundError(f'Scenarios directory not found: {scenarios_dir}')
        
        scenario_files = list(scenarios_dir.glob('*.glyph'))
        if not scenario_files:
            print(f'No .glyph files found in {scenarios_dir}')
            return
        
        print(f'Found {len(scenario_files)} scenario file(s)')
        
        for scenario_file in scenario_files:
            print(f'Processing {scenario_file.name}...')
            scenario_text = scenario_file.read_text()
            scenario = Scenario(scenario_text)
            
            summary = scenario.summarize(llm, template_manager)
            print(f'  Summary: {summary}')

