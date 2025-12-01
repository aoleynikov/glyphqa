# GlyphQA

An AI-powered test generation system that creates Playwright test specifications from natural language scenario descriptions.

## Overview

GlyphQA uses LLM agents to automatically build, analyze, and maintain Playwright test suites. You describe test scenarios in plain English (`.glyph` files), and the system generates executable Playwright test code.

## How It Works

### 1. Scenario Input
Write test scenarios in natural language as `.glyph` files:

```
log in as admin
go to users and create a new user
fill in the form with name, email, and role
submit the form
verify the user appears in the list
```

### 2. Iterative Build Process
The build agent works through scenarios step-by-step:

1. **Step Generation**: Converts the scenario into condensed, executable steps
2. **Incremental Building**: For each step:
   - Runs the current test to capture page state
   - Uses the page state to generate the next step's code
   - Updates the test specification
3. **Completion**: Once all steps are implemented, saves the final spec file

### 3. Key Principles

- **Condensed Steps**: Steps are grouped logically (e.g., "fill form and submit" is one step, not separate steps for each field)
- **Page State Capture**: After each step, the system captures the current page state to inform the next step
- **No Validation**: Scenarios build independently without dependency resolution or validation checks
- **Clean Output**: Generated specs contain only executable code - no comments, no debugging code

## Usage

### Build Tests
```bash
./glyph build
```

Build with verbose output:
```bash
./glyph build -v
```

### Purge Build Data
Clear all build progress and generated spec files:
```bash
./glyph purge
```

Force purge without confirmation:
```bash
./glyph purge -f
```

## Project Structure

- `scenarios/`: Input scenario files (`.glyph` format)
- `.glyph/`: Generated test files and build state
- `core/`: Main system components (agents, managers, tools)
- `prompts/`: Jinja2 templates for LLM interactions

## Workflow

1. **Write scenarios**: Create `.glyph` files describing your test cases
2. **Build**: Run `./glyph build` to generate Playwright specs
3. **Test**: Run the generated Playwright tests as needed

## Architecture

- **BuildAgent**: Orchestrates the iterative build process for scenarios
- **TemplateManager**: Manages Jinja2 prompts for LLM interactions
- **Tools**: Modular functions for execution, composition, and analysis
- **BuildProgress**: Tracks build state and scenario progress

The system is designed to be application-agnostic - it doesn't hardcode scenario specifics or test application implementation details into the code or prompts.

