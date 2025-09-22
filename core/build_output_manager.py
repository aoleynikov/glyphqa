"""
Build Output Manager - Provides clean, structured output during builds
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OutputLevel(Enum):
    """Output verbosity levels"""
    QUIET = 0      # Only errors and final results
    NORMAL = 1     # Key progress steps
    VERBOSE = 2    # Detailed debugging info
    DEBUG = 3      # All debug information

@dataclass
class BuildStep:
    """Represents a single build step"""
    name: str
    status: str  # "started", "completed", "failed", "skipped"
    details: Optional[str] = None
    duration: Optional[float] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BuildOutputManager:
    """
    Manages build output with different verbosity levels and structured reporting.
    """
    
    def __init__(self, level: OutputLevel = OutputLevel.NORMAL):
        self.level = level
        self.current_scenario = None
        self.current_step = None
        self.build_steps: List[BuildStep] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def set_level(self, level: OutputLevel):
        """Set the output verbosity level"""
        self.level = level
    
    def start_scenario(self, scenario_name: str):
        """Start building a new scenario"""
        self.current_scenario = scenario_name
        if self.level.value >= OutputLevel.NORMAL.value:
            print(f"\n🎯 Building: {scenario_name}")
    
    def start_step(self, step_name: str, step_type: str = "step"):
        """Start a new build step"""
        self.current_step = step_name
        if self.level.value >= OutputLevel.VERBOSE.value:
            print(f"  {step_type}: {step_name}")
    
    def complete_step(self, step_name: str, details: str = None):
        """Mark a step as completed"""
        if self.level.value >= OutputLevel.VERBOSE.value:
            status = "✅" if not details else f"✅ {details}"
            print(f"    {status}")
    
    def fail_step(self, step_name: str, error: str):
        """Mark a step as failed"""
        self.errors.append(f"{self.current_scenario}: {step_name} - {error}")
        if self.level.value >= OutputLevel.NORMAL.value:
            print(f"    ❌ {step_name}: {error}")
    
    def warn_step(self, step_name: str, warning: str):
        """Add a warning for a step"""
        self.warnings.append(f"{self.current_scenario}: {step_name} - {warning}")
        if self.level.value >= OutputLevel.NORMAL.value:
            print(f"    ⚠️  {step_name}: {warning}")
    
    def debug_info(self, message: str):
        """Output debug information"""
        if self.level.value >= OutputLevel.DEBUG.value:
            print(f"    🔍 {message}")
    
    def syntax_fix(self, file_path: str, fixes_applied: int):
        """Report syntax fixes"""
        if fixes_applied > 0 and self.level.value >= OutputLevel.NORMAL.value:
            print(f"    🔧 Fixed {fixes_applied} syntax errors in {file_path}")
    
    def sdk_update(self, function_name: str, module: str = None):
        """Report SDK function addition"""
        if self.level.value >= OutputLevel.VERBOSE.value:
            module_info = f" (module: {module})" if module else ""
            print(f"    📦 Added function '{function_name}'{module_info}")
    
    def page_state_capture(self, elements_count: int, step_name: str = None):
        """Report page state capture"""
        if self.level.value >= OutputLevel.DEBUG.value:
            step_info = f" for {step_name}" if step_name else ""
            print(f"    📄 Captured {elements_count} elements{step_info}")
    
    def reflection_step(self, elements_count: int, step_name: str):
        """Report reflection step"""
        if self.level.value >= OutputLevel.DEBUG.value:
            print(f"    🔄 Reflection: {elements_count} elements after {step_name}")
    
    def llm_call(self, purpose: str, success: bool = True):
        """Report LLM API calls"""
        if self.level.value >= OutputLevel.DEBUG.value:
            status = "✅" if success else "❌"
            print(f"    🤖 LLM {purpose}: {status}")
    
    def dependency_analysis(self, scenario: str, dependencies: List[str]):
        """Report dependency analysis"""
        if self.level.value >= OutputLevel.VERBOSE.value:
            deps_str = ", ".join(dependencies) if dependencies else "none"
            print(f"    📊 Dependencies: {deps_str}")
    
    def build_summary(self, total_scenarios: int = 0, successful_scenarios: int = 0):
        """Print final build summary"""
        print(f"\n📊 Build Summary:")
        print(f"  Scenarios: {successful_scenarios}/{total_scenarios}")
        print(f"  Steps: {len(self.build_steps)}")
        
        if self.errors:
            print(f"  ❌ Errors: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"    • {error}")
            if len(self.errors) > 5:
                print(f"    • ... and {len(self.errors) - 5} more errors")
        
        if self.warnings:
            print(f"  ⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings[:3]:  # Show first 3 warnings
                print(f"    • {warning}")
            if len(self.warnings) > 3:
                print(f"    • ... and {len(self.warnings) - 3} more warnings")
        
        if not self.errors and successful_scenarios == total_scenarios:
            print(f"  ✅ Build completed successfully!")
        else:
            print(f"  ❌ Build completed with errors")

# Global instance
build_output = BuildOutputManager()
