import yaml
from pathlib import Path


class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'glyph.config.yml'
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f'Config file not found: {config_path}')
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        self.scenarios_dir = data.get('scenarios_dir', 'scenarios')
        self.connection_url = data.get('connection', {}).get('url')
        self.llm_model = data.get('llm', {}).get('model')

