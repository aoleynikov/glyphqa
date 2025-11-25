from pathlib import Path
from core.config import Config
from core.template_manager import TemplateManager


def ensure_playwright_environment(base_url: str = None) -> Path:
    if base_url is None:
        config = Config()
        base_url = config.connection_url or 'http://localhost:3000'
    
    glyph_dir = Path('.glyph')
    glyph_dir.mkdir(exist_ok=True)
    
    template_manager = TemplateManager()
    expected_config = template_manager.playwright_config(base_url)
    expected_package_json = template_manager.package_json()
    
    config_path = glyph_dir / 'playwright.config.js'
    package_json_path = glyph_dir / 'package.json'
    
    needs_config_update = False
    needs_package_json = False
    
    if not config_path.exists():
        needs_config_update = True
    else:
        current_config = config_path.read_text()
        if current_config != expected_config:
            needs_config_update = True
    
    if not package_json_path.exists():
        needs_package_json = True
    
    if needs_config_update:
        config_path.write_text(expected_config)
    
    if needs_package_json:
        package_json_path.write_text(expected_package_json)
    
    return glyph_dir


ensure_playwright_environment()

