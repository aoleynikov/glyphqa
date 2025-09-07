# GlyphQA

Writing auto-tests shouldn't be more complex than explaining what you want to a human. "Log in with admin/4dm1n, go to Settings -> Users, create a user and add it to a group" maps to an autotest.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js and npm
- OpenAI API key (set in `glyph.config.yml`)

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

## Example

**Input** (`scenarios/create_user.glyph`):
```
Test user creation workflow

Login as administrator
Navigate to user management
Create a new user with name, email, and role
Verify the user appears in the list
```

## Architecture

```
Scenarios (.glyph) → Guides (.guide) → Playwright Tests (.spec.js)
     ↓                    ↓                    ↓
  LLM Parsing      Check-Specific Debug    HTML-Focused
  Step Structure   Spec Generation         Selectors
```
