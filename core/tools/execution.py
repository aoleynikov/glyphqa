import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from core.tools.composition import compose_spec, compose_spec_with_base
from core.playwright_env import ensure_playwright_environment
from core.config import Config
from core.template_manager import TemplateManager
from core.llm import LangChainLLM


@dataclass
class Outcome:
    outcome: str
    duration: float
    output: str


def run_playwright_spec(spec_path: str) -> Outcome:
    spec_file = Path(spec_path)
    if not spec_file.exists():
        raise FileNotFoundError(f'Spec file not found: {spec_path}')
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ['npx', 'playwright', 'test', str(spec_file), '--reporter=json'],
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        outcome = 'passed'
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired as e:
        outcome = 'timeout'
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or '')
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or '')
        output = stdout + stderr
    except subprocess.CalledProcessError as e:
        outcome = 'failed'
        output = e.stdout + e.stderr
    except Exception as e:
        outcome = 'error'
        output = str(e)
    
    duration = time.time() - start_time
    
    return Outcome(
        outcome=outcome,
        duration=duration,
        output=output
    )


def run_playwright_spec_tool(spec_path: str) -> str:
    result = run_playwright_spec(spec_path)
    return json.dumps({
        'outcome': result.outcome,
        'duration': result.duration,
        'output': result.output
    })


def run_steps_with_page_state(code_lines: str, base_url: str = None, llm: LangChainLLM = None, existing_spec: str = None) -> str:
    if base_url is None:
        config = Config()
        base_url = config.connection_url or 'http://localhost:3000'
    
    if llm is None:
        config = Config()
        llm = LangChainLLM(model=config.llm_model)
    
    template_manager = TemplateManager()
    capture_state_code = template_manager.capture_page_state_template(base_url=base_url)
    
    if existing_spec:
        if code_lines.strip():
            composed_code = compose_spec_with_base(existing_spec, code_lines, llm)
        else:
            composed_code = existing_spec
    else:
        if code_lines.strip():
            composed_code = compose_spec(base_url, code_lines, llm)
        else:
            composed_code = template_manager.step0_playwright_template(base_url=base_url)
    
    final_spec = compose_spec_with_base(composed_code, capture_state_code, llm)
    
    glyph_dir = ensure_playwright_environment(base_url)
    spec_path = glyph_dir / 'temp_state_capture.spec.js'
    spec_path.write_text(final_spec)
    
    result = run_playwright_spec(str(spec_path))
    
    return json.dumps({
        'outcome': result.outcome,
        'duration': result.duration,
        'output': result.output,
        'spec_code': final_spec
    })


def run_steps_with_page_state_tool(code_lines: str) -> str:
    return run_steps_with_page_state(code_lines)

