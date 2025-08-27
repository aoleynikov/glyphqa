#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.scenario_builder import ScenarioBuilder
from core.system_catalog import SystemCatalog
from core.filesystem import FileSystem
from core.target import PlaywrightTarget
from core.llm import OpenAIProvider
from core.config import Config

def test_iteration_with_system_catalog():
    """Test that the iteration process can use SystemCatalog to find correct button text."""
    
    print("Testing iteration process with SystemCatalog integration...")
    
    # Initialize components
    config = Config('glyph.config.yml')
    filesystem = FileSystem()
    target = PlaywrightTarget(config)
    llm_provider = config.llm
    
    # Initialize SystemCatalog with test data
    catalog = SystemCatalog(filesystem)
    
    # Add test page data to catalog (simulating what would be captured during build)
    dashboard_page_data = {
        "url": "http://localhost:3000/",
        "title": "React App",
        "elements": [
            {
                "tag": "button",
                "type": "submit",
                "name": None,
                "textContent": "Create New User",
                "visible": True,
                "enabled": True,
                "selectors": {
                    "byText": "text=\"Create New User\""
                }
            },
            {
                "tag": "a",
                "type": None,
                "name": None,
                "textContent": "Users",
                "href": "http://localhost:3000/#",
                "visible": True,
                "enabled": True,
                "selectors": {
                    "byText": "text=\"Users\"",
                    "byHref": "a[href=\"http://localhost:3000/#\"]"
                }
            }
        ],
        "formElements": [
            {
                "tag": "button",
                "type": "submit",
                "textContent": "Create New User"
            }
        ],
        "navigationElements": [
            {
                "tag": "a",
                "textContent": "Users"
            }
        ]
    }
    
    # Catalog the dashboard page
    catalog.catalog_page_state(
        url="http://localhost:3000/",
        page_data=dashboard_page_data,
        action_context="navigate to users"
    )
    
    # Get system insights
    system_insights = catalog.get_system_insights()
    print(f"\nSystem Insights:\n{system_insights}")
    
    # Test the iteration prompt generation
    builder = ScenarioBuilder(target, config)
    builder.llm_provider = llm_provider
    builder.system_catalog = catalog
    
    # Simulate the current state
    current_spec = """import { test, expect } from '@playwright/test';

test.describe('User Creation', () => {
  test('should create a new user', async ({ page }) => {
    await page.goto('/');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin_password');
    await page.click('text="Login"');
    await page.waitForSelector('text="Users"', { state: 'visible' });
    await page.click('text="Users"');
  });
});"""
    
    implemented_actions = [
        "navigate to login page",
        "type admin as username", 
        "type admin_password as password",
        "click login button",
        "navigate to users"
    ]
    
    # Simulate page state after the last action
    page_dump = """Current URL: http://localhost:3000/
Page Title: React App
Page State: {
  "url": "http://localhost:3000/",
  "title": "React App",
  "elements": [
    {
      "tag": "button",
      "type": "submit",
      "name": null,
      "textContent": "Create New User",
      "visible": true,
      "enabled": true,
      "selectors": {
        "byText": "text=\\"Create New User\\""
      }
    },
    {
      "tag": "a",
      "type": null,
      "name": null,
      "textContent": "Users",
      "href": "http://localhost:3000/#",
      "visible": true,
      "enabled": true,
      "selectors": {
        "byText": "text=\\"Users\\"",
        "byHref": "a[href=\\"http://localhost:3000/#\\"]"
      }
    }
  ],
  "formElements": [
    {
      "tag": "button",
      "type": "submit",
      "textContent": "Create New User"
    }
  ],
  "navigationElements": [
    {
      "tag": "a",
      "textContent": "Users"
    }
  ]
}"""
    
    # Generate page summary
    page_summary = builder._generate_page_summary(page_dump)
    print(f"\nPage Summary: {page_summary}")
    
    # Generate iteration prompt
    iteration_prompt = builder._generate_iteration_prompt(
        current_spec=current_spec,
        implemented_actions=implemented_actions,
        page_dump=page_dump,
        page_summary=page_summary,
        system_insights=system_insights
    )
    
    print(f"\nIteration Prompt Length: {len(iteration_prompt)} characters")
    
    # Check if the prompt contains the correct button text
    if "Create New User" in iteration_prompt:
        print("✅ Iteration prompt contains correct button text 'Create New User'")
    else:
        print("❌ Iteration prompt missing correct button text")
    
    if "Add New User" in iteration_prompt:
        print("❌ Iteration prompt contains incorrect button text 'Add New User'")
    else:
        print("✅ Iteration prompt does not contain incorrect button text")
    
    # Check if system insights are included
    if "Create New User" in system_insights:
        print("✅ System insights contain correct button text")
    else:
        print("❌ System insights missing correct button text")
    
    # Test the action context generation
    all_actions = [
        "navigate to login page",
        "type admin as username",
        "type admin_password as password", 
        "click login button",
        "navigate to users",
        "click \"Add New User\"",  # This is the problematic action from the guide
        "type in username",
        "type in email",
        "type in password",
        "select role = user",
        "submit the form"
    ]
    
    action_context = builder._update_spec_with_action(
        iteration_prompt=iteration_prompt,
        action="click \"Add New User\"",  # The guide action
        all_actions=all_actions,
        current_action_index=5  # Index of the problematic action
    )
    
    print(f"\nAction Context Length: {len(action_context)} characters")
    
    # The key test: does the iteration process have enough information to correct the button text?
    print(f"\nKey Question: Can the iteration process use SystemCatalog to correct 'Add New User' to 'Create New User'?")
    print(f"System Insights available: {len(system_insights)} characters")
    print(f"Page State available: {len(page_dump)} characters")
    print(f"Page Summary: {page_summary}")
    
    # Check if the prompt has clear instructions about using page state over scenario text
    if "PRIORITIZE SYSTEM KNOWLEDGE OVER SCENARIO TEXT" in iteration_prompt:
        print("✅ Prompt has clear instructions to prioritize system knowledge")
    else:
        print("❌ Prompt missing instructions to prioritize system knowledge")
    
    if "IGNORE scenario text if page state clearly shows target elements" in iteration_prompt:
        print("✅ Prompt has clear instructions to ignore scenario text when page state shows elements")
    else:
        print("❌ Prompt missing instructions to ignore scenario text")
    
    if "Create New User" in page_dump:
        print("✅ Page state contains correct button text")
    else:
        print("❌ Page state missing correct button text")

if __name__ == "__main__":
    test_iteration_with_system_catalog()
