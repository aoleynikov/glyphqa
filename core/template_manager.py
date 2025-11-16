import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class TemplateManager:
    def __init__(self, templates_dir=None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / 'prompts'
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))
    
    def scenario_to_steps(self, scenario_text):
        template = self.env.get_template('scenario_to_steps.j2')
        return template.render(scenario_text=scenario_text)
    
    def scenario_summarize(self, scenario_text):
        template = self.env.get_template('scenario_summarize.j2')
        return template.render(scenario_text=scenario_text)
    
    def find_scenario_references(self, scenario, scenario_summaries):
        template = self.env.get_template('find_scenario_references.j2')
        return template.render(scenario=scenario, scenario_summaries=scenario_summaries)
    
    def is_scenario_required(self, scenario_a, scenario_b):
        template = self.env.get_template('is_scenario_required.j2')
        return template.render(scenario_a=scenario_a, scenario_b=scenario_b)

