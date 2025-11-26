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
    
    def check_scenario_reference_system_prompt(self):
        template = self.env.get_template('check_scenario_reference_system.j2')
        return template.render()
    
    def check_scenario_reference_user_prompt(self, scenario_a, scenario_b):
        template = self.env.get_template('check_scenario_reference_user.j2')
        return template.render(scenario_a=scenario_a, scenario_b=scenario_b)
    
    def agent_system_prompt(self):
        template = self.env.get_template('agent_system_prompt.j2')
        return template.render()
    
    def step0_playwright_template(self, base_url):
        template = self.env.get_template('step0_playwright_template.j2')
        return template.render(base_url=base_url)
    
    def playwright_config(self, base_url):
        template = self.env.get_template('playwright.config.js.j2')
        return template.render(base_url=base_url)
    
    def package_json(self):
        template = self.env.get_template('package.json.j2')
        return template.render()
    
    def compose_spec_system_prompt(self):
        template = self.env.get_template('compose_spec_system.j2')
        return template.render()
    
    def compose_spec_user_prompt(self, base_code, additional_code):
        template = self.env.get_template('compose_spec_user.j2')
        return template.render(base_code=base_code, additional_code=additional_code)
    
    def capture_page_state_template(self, base_url):
        template = self.env.get_template('capture_page_state.j2')
        return template.render(base_url=base_url)
    
    def analyze_spec_implementation_system_prompt(self):
        template = self.env.get_template('analyze_spec_implementation_system.j2')
        return template.render()
    
    def analyze_spec_implementation_user_prompt(self, spec_code, scenario_text):
        template = self.env.get_template('analyze_spec_implementation_user.j2')
        return template.render(spec_code=spec_code, scenario_text=scenario_text)
    
    def generate_next_code_system_prompt(self):
        template = self.env.get_template('generate_next_code_system.j2')
        return template.render()
    
    def generate_next_code_user_prompt(self, page_state_output, next_step_guidance):
        template = self.env.get_template('generate_next_code_user.j2')
        return template.render(page_state_output=page_state_output, next_step_guidance=next_step_guidance)
    
    def list_scenarios(self, scenarios):
        template = self.env.get_template('list_scenarios.j2')
        return template.render(scenarios=scenarios)
    
    def build_next_step_system_prompt(self):
        template = self.env.get_template('build_next_step_system.j2')
        return template.render()
    
    def build_next_step_user_prompt(self, all_scenarios, current_scenario_name, current_scenario_path, current_scenario_text, step_list, completed_steps_indices, current_spec, page_state_output):
        template = self.env.get_template('build_next_step_user.j2')
        return template.render(
            all_scenarios=all_scenarios,
            current_scenario_name=current_scenario_name,
            current_scenario_path=current_scenario_path,
            current_scenario_text=current_scenario_text,
            step_list=step_list,
            completed_steps_indices=completed_steps_indices,
            current_spec=current_spec,
            page_state_output=page_state_output
        )
    
    def validate_scenario_implementation_system_prompt(self):
        template = self.env.get_template('validate_scenario_implementation_system.j2')
        return template.render()
    
    def validate_scenario_implementation_user_prompt(self, scenario_text, spec_code):
        template = self.env.get_template('validate_scenario_implementation_user.j2')
        return template.render(scenario_text=scenario_text, spec_code=spec_code)

