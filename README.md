# GlyphQA

**Turn natural language scenarios into Playwright tests with AI**

GlyphQA converts human-readable test scenarios into executable Playwright test suites using LLM-driven code generation.

## Main Idea

Write test scenarios in plain English, and GlyphQA generates the corresponding Playwright automation code. The system uses AI to understand your scenarios, break them down into actionable steps, and create robust test implementations.

## Use Cases

- **Rapid Test Creation**: Convert manual test cases to automated tests quickly
- **Non-Technical Test Writing**: Let QA engineers write tests in natural language
- **Test Documentation**: Scenarios serve as both tests and documentation
- **Regression Testing**: Automatically generate comprehensive test suites

## Quick Start

1. **Write a scenario** in `scenarios/login.glyph`:
```
navigate to the login page
use login/pass123
you should be taken to the dashboard
```

2. **Generate guides and build tests**:
```bash
python3 glyph load
python3 glyph build --scenario login.glyph
```

3. **Run the tests**:
```bash
python3 glyph test --scenario login.glyph
```

## Commands

- `glyph load` - Generate guides from scenarios
- `glyph build [--scenario FILE]` - Build Playwright tests
- `glyph test [--scenario FILE]` - Run tests (all or specific scenario)
- `glyph purge` - Clear cache and start fresh

## Features

- **Smart Caching**: Only rebuilds when scenarios change
- **Dependency Resolution**: Automatically handles scenario references
- **LLM-Driven**: Uses AI for intelligent code generation
- **Playwright Integration**: Generates production-ready test code
- **Reference System**: Reuse common workflows across scenarios

## Example

**Input** (`scenarios/create_user.glyph`):
```
Test user creation workflow

Login as administrator
Navigate to user management
Create a new user with name, email, and role
Verify the user appears in the list
```

**Output**: Executable Playwright test that logs in, navigates to user management, fills the form, submits it, and verifies the result.

---

*GlyphQA bridges the gap between human-readable test scenarios and automated test execution.*
