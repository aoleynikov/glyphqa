from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class TemplateManager:
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / 'prompts'
        self.env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render_template(self, template_path: str, **kwargs) -> str:
        """Render a Jinja2 template with the given context variables."""
        template = self.env.get_template(template_path)
        return template.render(**kwargs)
    
    def get_playwright_template(self, template_name: str, **kwargs) -> str:
        """Convenience method for rendering Playwright target templates."""
        template_path = f'targets/playwright/{template_name}.j2'
        return self.render_template(template_path, **kwargs)
    
    def get_scenario_template(self, template_name: str, **kwargs) -> str:
        """Convenience method for rendering scenario templates."""
        template_path = f'scenarios/{template_name}.j2'
        return self.render_template(template_path, **kwargs)
