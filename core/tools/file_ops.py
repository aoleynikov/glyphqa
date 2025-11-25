import json
from pathlib import Path
from core.playwright_env import ensure_playwright_environment


def save_spec(spec_code: str, filename: str) -> str:
    glyph_dir = ensure_playwright_environment()
    
    if not filename.endswith('.spec.js'):
        filename = f'{filename}.spec.js'
    
    spec_path = glyph_dir / filename
    spec_path.write_text(spec_code)
    
    return json.dumps({
        'success': True,
        'path': str(spec_path),
        'filename': filename
    })


def read_spec(filename: str) -> str:
    glyph_dir = Path('.glyph')
    
    if not filename.endswith('.spec.js'):
        filename = f'{filename}.spec.js'
    
    spec_path = glyph_dir / filename
    
    if not spec_path.exists():
        return json.dumps({
            'success': False,
            'error': f'Spec file not found: {filename}'
        })
    
    spec_code = spec_path.read_text()
    
    return json.dumps({
        'success': True,
        'filename': filename,
        'spec_code': spec_code
    })


def save_spec_tool(spec_code: str, filename: str) -> str:
    return save_spec(spec_code, filename)


def read_spec_tool(filename: str) -> str:
    return read_spec(filename)


def ls_path(path: str) -> str:
    target_path = Path(path)
    
    if not target_path.exists():
        return json.dumps({
            'success': False,
            'error': f'Path not found: {path}'
        })
    
    if target_path.is_file():
        return json.dumps({
            'success': True,
            'type': 'file',
            'path': str(target_path),
            'name': target_path.name
        })
    
    items = []
    for item in sorted(target_path.iterdir()):
        items.append({
            'name': item.name,
            'type': 'file' if item.is_file() else 'directory',
            'path': str(item)
        })
    
    return json.dumps({
        'success': True,
        'type': 'directory',
        'path': str(target_path),
        'items': items
    })


def ls_path_tool(path: str) -> str:
    return ls_path(path)

