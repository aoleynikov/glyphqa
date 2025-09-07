from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Step(ABC):
    """Base class for all test steps."""
    
    def __init__(self, description: str, step_type: str):
        self.description = description
        self.step_type = step_type
    
    @abstractmethod
    def to_playwright(self) -> str:
        """Convert step to Playwright code."""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.description})"


class Action(Step):
    """Represents an action the user performs."""
    
    def __init__(self, description: str, action_type: str, target: str = None, data: Dict[str, Any] = None):
        super().__init__(description, "action")
        self.action_type = action_type
        self.target = target or ""
        self.data = data or {}
    
    def to_playwright(self, llm_provider=None, template_manager=None) -> str:
        """Convert action to Playwright code using LLM."""
        if llm_provider and template_manager:
            # Use LLM to generate Playwright code
            context = {
                'action_type': self.action_type,
                'description': self.description,
                'target': self.target,
                'data': self.data
            }
            system_prompt = template_manager.get_playwright_template("action_converter", **context)
            return llm_provider.generate(system_prompt, self.description)
        else:
            # Fallback for when LLM is not available
            return f'// TODO: Implement {self.action_type} for {self.target}'
    
    def __repr__(self):
        return f"Action({self.action_type}: {self.description})"


class Check(Step):
    """Represents a verification/assertion."""
    
    def __init__(self, description: str, check_type: str, target: str = None, expected: str = None, is_explicit: bool = True):
        super().__init__(description, "check")
        self.check_type = check_type
        self.target = target or ""
        self.expected = expected or ""
        self.is_explicit = is_explicit
    
    def to_playwright(self, llm_provider=None, template_manager=None, page_analysis=None) -> str:
        """Convert check to Playwright code using LLM with optional page analysis."""
        if llm_provider and template_manager:
            # Use LLM to generate Playwright code
            context = {
                'check_type': self.check_type,
                'description': self.description,
                'target': self.target,
                'expected': self.expected,
                'is_explicit': self.is_explicit
            }
            
            # Add page analysis if available
            if page_analysis:
                context['page_analysis'] = page_analysis
            
            system_prompt = template_manager.get_playwright_template("check_converter", **context)
            return llm_provider.generate(system_prompt, self.description)
        else:
            # Fallback for when LLM is not available
            return f'// TODO: Implement {self.check_type} check for {self.target}'
    
    def __repr__(self):
        explicit_flag = "explicit" if self.is_explicit else "baseline"
        return f"Check({self.check_type}, {explicit_flag}: {self.description})"


class StepList:
    """Container for managing a list of steps."""
    
    def __init__(self, steps: list = None):
        self.steps = steps or []
    
    def add_action(self, description: str, action_type: str, target: str = None, data: Dict[str, Any] = None):
        """Add an action step."""
        action = Action(description, action_type, target, data)
        self.steps.append(action)
        return action
    
    def add_check(self, description: str, check_type: str, target: str = None, expected: str = None, is_explicit: bool = True):
        """Add a check step."""
        check = Check(description, check_type, target, expected, is_explicit)
        self.steps.append(check)
        return check
    
    def add_baseline_checks(self):
        """Add baseline technical checks to the step list."""
        baseline_checks = [
            Check("no console errors", "console_error", is_explicit=False),
            Check("page loaded successfully", "page_load", is_explicit=False)
        ]
        
        # Add baseline checks at the end
        for check in baseline_checks:
            self.steps.append(check)
    
    def get_actions(self) -> list:
        """Get all action steps."""
        return [step for step in self.steps if isinstance(step, Action)]
    
    def get_checks(self) -> list:
        """Get all check steps."""
        return [step for step in self.steps if isinstance(step, Check)]
    
    def get_explicit_checks(self) -> list:
        """Get only explicit check steps."""
        return [step for step in self.steps if isinstance(step, Check) and step.is_explicit]
    
    def get_baseline_checks(self) -> list:
        """Get only baseline check steps."""
        return [step for step in self.steps if isinstance(step, Check) and not step.is_explicit]
    
    def to_playwright(self, llm_provider=None, template_manager=None) -> str:
        """Convert all steps to Playwright code."""
        playwright_code = []
        for step in self.steps:
            code = step.to_playwright(llm_provider, template_manager)
            if code:
                playwright_code.append(code)
        return '\n    '.join(playwright_code)
    
    def __len__(self):
        return len(self.steps)
    
    def __iter__(self):
        return iter(self.steps)
    
    def __repr__(self):
        return f"StepList({len(self.steps)} steps)"
