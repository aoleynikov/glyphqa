from langchain.tools import StructuredTool
from core.tools.execution import run_playwright_spec_tool, run_steps_with_page_state_tool
from core.tools.composition import compose_spec_tool
from core.tools.file_ops import save_spec_tool, read_spec_tool, ls_path_tool
from core.tools.analysis import analyze_spec_implementation_tool
from core.tools.progress import (
    read_build_progress_tool,
    get_scenario_status_tool,
    get_not_yet_implemented_scenarios_tool,
    update_scenario_status_tool,
)
from core.tools.generation import generate_next_code_tool


def create_playwright_tool():
    return StructuredTool.from_function(
        func=run_playwright_spec_tool,
        name='run_playwright_spec',
        description='Runs a Playwright test spec file and returns a JSON object with outcome (passed/failed/timeout/error), duration in seconds, and output text. Takes a file path as input.'
    )


def create_compose_spec_tool():
    return StructuredTool.from_function(
        func=compose_spec_tool,
        name='compose_spec',
        description='Composes a Playwright test spec by combining the step0 template (with base URL setup) with additional test code. Takes base_url (string) and additional_code (string) as inputs. Returns the complete composed spec code.'
    )


def create_run_steps_with_page_state_tool():
    return StructuredTool.from_function(
        func=run_steps_with_page_state_tool,
        name='run_steps_with_page_state',
        description='Runs test steps and captures page state. Takes code_lines (string) as input - the test code steps to execute. Combines step0 template + code_lines + page state capture, runs the test, and returns a JSON object with outcome, duration, output, and the generated spec_code.'
    )


def create_save_spec_tool():
    return StructuredTool.from_function(
        func=save_spec_tool,
        name='save_spec',
        description='Saves a Playwright test spec code to a file in the .glyph directory. Takes spec_code (string) and filename (string) as inputs. The filename will have .spec.js appended if not already present. Returns a JSON object with success status, path, and filename.'
    )


def create_read_spec_tool():
    return StructuredTool.from_function(
        func=read_spec_tool,
        name='read_spec',
        description='Reads a Playwright test spec file from the .glyph directory. Takes filename (string) as input. The filename will have .spec.js appended if not already present. Returns a JSON object with success status, filename, and spec_code (if successful) or error message (if file not found).'
    )


def create_analyze_spec_implementation_tool():
    return StructuredTool.from_function(
        func=analyze_spec_implementation_tool,
        name='analyze_spec_implementation',
        description='Analyzes how well a Playwright test spec implements a given scenario. Takes spec_code (string) and scenario_text (string) as inputs. Returns a JSON object with implementation_status, completed_steps, missing_steps, next_steps, and notes.'
    )


def create_ls_path_tool():
    return StructuredTool.from_function(
        func=ls_path_tool,
        name='ls_path',
        description='Lists files and directories at the given path. Takes path (string) as input. Returns a JSON object with success status, type (file/directory), path, and items (if directory) or name (if file). Returns error if path not found.'
    )


def create_read_build_progress_tool():
    return StructuredTool.from_function(
        func=read_build_progress_tool,
        name='read_build_progress',
        description='Reads the current build progress state. Returns a JSON object with all scenarios, their statuses, and lists of scenarios by status (not_yet_implemented, in_progress, completed, failed).'
    )


def create_get_scenario_status_tool():
    return StructuredTool.from_function(
        func=get_scenario_status_tool,
        name='get_scenario_status',
        description='Gets the current status and details of a specific scenario. Takes scenario_name (string) as input. Returns a JSON object with scenario details including status, dependencies, error_message, and spec_file_path.'
    )


def create_get_not_yet_implemented_scenarios_tool():
    return StructuredTool.from_function(
        func=get_not_yet_implemented_scenarios_tool,
        name='get_not_yet_implemented_scenarios',
        description='Gets a list of all scenarios that are not yet implemented. Returns a JSON object with a list of scenario names and count.'
    )


def create_update_scenario_status_tool():
    return StructuredTool.from_function(
        func=update_scenario_status_tool,
        name='update_scenario_status',
        description='Updates the status of a scenario. Takes scenario_name (string), status (string: in_progress/completed/failed), optional error_message (string), and optional spec_file_path (string) as inputs. Returns a JSON object with success status.'
    )


def create_generate_next_code_tool():
    return StructuredTool.from_function(
        func=generate_next_code_tool,
        name='generate_next_code',
        description='Generates Playwright test code based on page state and implementation guidance. Takes page_state_output (string) - the output from running a test that captured page state, and next_step_guidance (string) - guidance on what to implement next. Returns a JSON object with the generated code.'
    )

