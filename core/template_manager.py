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

