from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
import json
import subprocess
import logging
from .templates import TemplateManager
from .scenario_builder import ScenarioBuilder

logger = logging.getLogger(__name__)


class Target(ABC):
    def __init__(self, name: str, config=None):
        self.name = name
        self.config = config
    
    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name})'


class PlaywrightTarget(Target):
    def __init__(self, config=None):
        super().__init__('playwright', config)
        self.version = '1.40.0'
        self.template_manager = TemplateManager()
    
    def get_system_prompt(self) -> str:
        return "You are an expert automation engineer specializing in web automation."
    

    



    
    def run_debug_spec(self, spec_content: str) -> str:
        """Run a debug version of the spec and capture comprehensive page state."""
        debug_filepath = Path('.glyph/tests/debug.spec.js')
        
        with open(debug_filepath, 'w') as f:
            f.write(spec_content)
        
        try:
            result = subprocess.run(
                ['npm', 'test', 'debug.spec.js'],
                cwd=Path('.glyph'),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Extract URL, title, and page state from console output
            output_lines = result.stdout.split('\n')
            url = None
            title = None
            page_state_json = None
            
            for line in output_lines:
                if 'Current URL:' in line:
                    url = line.split('Current URL:')[1].strip()
                elif 'Page Title:' in line:
                    title = line.split('Page Title:')[1].strip()
                elif 'Page State:' in line:
                    # Extract the JSON page state
                    json_start = line.find('{')
                    if json_start != -1:
                        try:
                            page_state_json = line[json_start:]
                            # Try to parse to validate JSON
                            import json
                            json.loads(page_state_json)
                        except json.JSONDecodeError:
                            # If it's multiline JSON, try to reconstruct
                            page_state_json = None
            
            # If we didn't get the JSON in one line, try to reconstruct from multiple lines
            if not page_state_json:
                json_lines = []
                in_json = False
                for line in output_lines:
                    if 'Page State:' in line:
                        in_json = True
                        json_start = line.find('{')
                        if json_start != -1:
                            json_lines.append(line[json_start:])
                    elif in_json and line.strip():
                        json_lines.append(line.strip())
                        if line.strip().endswith('}'):
                            break
                
                if json_lines:
                    try:
                        page_state_json = ''.join(json_lines)
                        import json
                        json.loads(page_state_json)  # Validate
                    except json.JSONDecodeError:
                        page_state_json = None
            
            # Build comprehensive page state output
            page_dump = f"Current URL: {url}\nPage Title: {title}"
            
            if page_state_json:
                page_dump += f"\n\nComprehensive Page State:\n{page_state_json}"
            
            page_dump += f"\n\nTest Output:\n{result.stdout}"
            
            return page_dump
            
        except subprocess.TimeoutExpired:
            return "Test timed out - page may not be accessible"
        except Exception as e:
            return f"Test execution failed: {str(e)}"
    


    def build_scenario(self, scenario, debug_stop=None):
        """Build Playwright test by delegating to ScenarioBuilder."""
        builder = ScenarioBuilder(self, self.config)
        return builder.build_scenario(scenario, debug_stop=debug_stop)
    
    def init(self):
        """Initialize Playwright test suite in .glyph folder."""
        glyph_dir = Path('.glyph')
        if glyph_dir.exists():
            import shutil
            # Preserve guides directory if it exists
            guides_dir = glyph_dir / 'guides'
            guides_backup = None
            if guides_dir.exists():
                import tempfile
                guides_backup = tempfile.mkdtemp()
                shutil.copytree(guides_dir, Path(guides_backup) / 'guides')
                logger.info('Backed up existing guides directory')
            
            shutil.rmtree(glyph_dir)
            logger.info('Removed existing .glyph directory')
            
            # Restore guides directory
            if guides_backup:
                glyph_dir.mkdir()
                shutil.copytree(Path(guides_backup) / 'guides', glyph_dir / 'guides')
                shutil.rmtree(guides_backup)
                logger.info('Restored guides directory')
        
        # Create .glyph directory structure
        glyph_dir.mkdir(exist_ok=True)
        tests_dir = glyph_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        # Create package.json
        package_json = {
            "name": "glyph-playwright-tests",
            "version": "1.0.0",
            "description": "Playwright tests generated by GlyphQA",
            "scripts": {
                "test": "playwright test",
                "test:headed": "playwright test --headed",
                "test:debug": "playwright test --debug"
            },
            "devDependencies": {
                "@playwright/test": "^1.40.0"
            }
        }
        
        import json
        with open(glyph_dir / 'package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        logger.info('  - Created package.json')
        
        # Create playwright.config.js
        config_content = f'''const {{ defineConfig, devices }} = require('@playwright/test');

module.exports = defineConfig({{
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {{
    baseURL: '{self.config.connection.url}',
    trace: 'on-first-retry',
  }},
  projects: [
    {{
      name: 'chromium',
      use: {{ ...devices['Desktop Chrome'] }},
    }},
  ],
}});
'''
        
        with open(glyph_dir / 'playwright.config.js', 'w') as f:
            f.write(config_content)
        logger.info('  - Created playwright.config.js')
        logger.info(f'  - Set baseURL to: {self.config.connection.url}')
        logger.info('  - Created tests/ directory')
        
        # Install dependencies
        logger.info('\nInstalling dependencies...')
        try:
            import subprocess
            result = subprocess.run(['npm', 'install'], cwd=glyph_dir, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info('  ✓ Installed npm packages')
            else:
                logger.error(f'  ✗ Failed to install npm packages: {result.stderr}')
                raise Exception('npm install failed')
            
            result = subprocess.run(['npx', 'playwright', 'install'], cwd=glyph_dir, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.info('  ✓ Installed Playwright browsers')
            else:
                logger.error(f'  ✗ Failed to install Playwright browsers: {result.stderr}')
                raise Exception('playwright install failed')
                
        except subprocess.TimeoutExpired:
            logger.error('  ✗ Installation timed out')
            raise Exception('Installation timed out')
        except Exception as e:
            logger.error(f'  ✗ Installation failed: {e}')
            raise
        
        logger.info('\nPlaywright test suite is ready to run!')
        logger.info('Use: cd .glyph && npm test')
