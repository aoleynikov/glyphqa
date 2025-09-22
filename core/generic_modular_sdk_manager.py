"""
Generic Modular SDK Manager - Works for any application
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .generic_function_classifier import GenericFunctionClassifier, FunctionClassification

logger = logging.getLogger(__name__)

@dataclass
class ModuleInfo:
    """Information about a SDK module."""
    name: str
    path: str
    description: str
    function_count: int
    last_updated: str

class GenericModularSdkManager:
    """
    Generic modular SDK manager that works for any application.
    
    Responsibilities:
    - Organize functions into logical modules
    - Maintain module structure
    - Generate modular SDK files
    - Handle function dependencies
    - Provide SDK information
    """
    
    def __init__(self, sdk_dir: Path, template_manager, filesystem, llm_provider=None):
        self.sdk_dir = Path(sdk_dir)
        self.template_manager = template_manager
        self.filesystem = filesystem
        self.llm_provider = llm_provider
        
        # Initialize classifier
        self.classifier = GenericFunctionClassifier(llm_provider, template_manager)
        
        # Module structure
        self.modules_dir = self.sdk_dir / 'modules'
        self.modules_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing modules
        self.modules = self._load_existing_modules()
    
    def _load_existing_modules(self) -> Dict[str, List[Dict]]:
        """Load existing modules from the SDK directory."""
        modules = {}
        
        if not self.modules_dir.exists():
            return modules
        
        for module_dir in self.modules_dir.iterdir():
            if module_dir.is_dir():
                module_name = module_dir.name
                modules[module_name] = []
                
                # Load functions from module
                for js_file in module_dir.glob("*.js"):
                    if js_file.name != 'index.js':
                        # This would parse the JS file and extract function info
                        # For now, we'll skip this complexity
                        pass
        
        return modules
    
    def add_function(self, function_data: Dict[str, Any]) -> bool:
        """
        Add a function to the appropriate module.
        
        Args:
            function_data: Dictionary with function information
            
        Returns:
            bool: True if successfully added
        """
        try:
            # Validate and fix function content
            from .node_syntax_checker import NodeSyntaxChecker
            validator = NodeSyntaxChecker()
            
            function_content = function_data.get('content', '')
            is_valid, errors = validator.check_syntax(function_content)
            
            if not is_valid:
                logger.warning(f"Function '{function_data.get('name')}' has syntax errors: {errors}")
                # Try to fix the function content
                fixed_content, fixes_applied = validator.fix_syntax_errors(function_content)
                
                if fixes_applied > 0:
                    logger.info(f"Fixed {fixes_applied} syntax errors in function '{function_data.get('name')}'")
                    function_data['content'] = fixed_content
                else:
                    logger.error(f"Could not fix syntax errors in function '{function_data.get('name')}': {errors}")
                    return False
            
            # Classify the function
            classification = self.classifier.classify_function(
                function_data.get('name', ''),
                function_content,
                function_data.get('type', ''),
                function_data.get('application_context', '')
            )
            
            # Add to appropriate module
            module_name = classification.suggested_module
            if module_name not in self.modules:
                self.modules[module_name] = []
            
            # Ensure function_data has all required fields for template rendering
            function_data['to_composable_js'] = lambda: function_content
            function_data['summary'] = function_data.get('summary', 'No description available')
            function_data['function_type'] = function_data.get('type', 'unknown')
            
            self.modules[module_name].append(function_data)
            
            # Generate module files
            self._generate_module_files()
            
            # Run iterative syntax fixer on the generated SDK
            self._fix_sdk_syntax()
            
            logger.info(f"✅ Added function '{function_data.get('name')}' to module '{module_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add function: {e}")
            return False
    
    def _fix_sdk_syntax(self) -> None:
        """Run Node.js-based syntax fixer on the generated SDK files."""
        try:
            from .node_syntax_checker import NodeSyntaxChecker
            checker = NodeSyntaxChecker()
            
            # Fix main SDK file
            sdk_file = self.sdk_dir / 'index.js'
            if sdk_file.exists():
                is_valid, errors = checker.check_file(str(sdk_file))
                if not is_valid:
                    with open(sdk_file, 'r') as f:
                        content = f.read()
                    fixed_content, fixes_applied = checker.fix_syntax_errors(content)
                    if fixes_applied > 0:
                        with open(sdk_file, 'w') as f:
                            f.write(fixed_content)
                        logger.info(f"🔧 Fixed {fixes_applied} syntax errors in main SDK")
            
            # Fix module files
            for module_name in self.modules.keys():
                module_file = self.sdk_dir / 'modules' / module_name / 'index.js'
                if module_file.exists():
                    is_valid, errors = checker.check_file(str(module_file))
                    if not is_valid:
                        with open(module_file, 'r') as f:
                            content = f.read()
                        fixed_content, fixes_applied = checker.fix_syntax_errors(content)
                        if fixes_applied > 0:
                            with open(module_file, 'w') as f:
                                f.write(fixed_content)
                            logger.info(f"🔧 Fixed {fixes_applied} syntax errors in {module_name} module")
                        
        except Exception as e:
            logger.warning(f"Failed to run Node.js syntax fixer: {e}")
    
    def _generate_module_files(self) -> None:
        """Generate all module files."""
        for module_name, functions in self.modules.items():
            if functions:
                self._generate_module_file(module_name, functions)
        
        # Generate main SDK index
        self._generate_main_index()
    
    def _generate_module_file(self, module_name: str, functions: List[Dict]) -> None:
        """Generate a module file."""
        module_dir = self.modules_dir / module_name
        module_dir.mkdir(exist_ok=True)
        
        # Generate module content
        module_content = self.template_manager.render_template(
            'targets/playwright/generic_module.j2',
            module_description=f"{module_name.title()} functions",
            functions=functions
        )
        
        # Write module file
        module_file = module_dir / 'index.js'
        self.filesystem.write_text(str(module_file), module_content)
    
    def _generate_main_index(self) -> None:
        """Generate the main SDK index file."""
        index_content = self.template_manager.render_template(
            'targets/playwright/generic_sdk_index.j2',
            modules=self.modules
        )
        
        # Write main index
        index_file = self.sdk_dir / 'index.js'
        self.filesystem.write_text(str(index_file), index_content)
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """Get information about a specific module."""
        if module_name not in self.modules:
            return None
        
        functions = self.modules[module_name]
        module_dir = self.modules_dir / module_name
        
        return ModuleInfo(
            name=module_name,
            path=str(module_dir),
            description=f"{module_name.title()} functions",
            function_count=len(functions),
            last_updated="unknown"  # Would track this in real implementation
        )
    
    def get_all_modules(self) -> List[ModuleInfo]:
        """Get information about all modules."""
        return [
            self.get_module_info(module_name) 
            for module_name in self.modules.keys()
        ]
    
    def get_functions_by_module(self, module_name: str) -> List[Dict]:
        """Get all functions in a specific module."""
        return self.modules.get(module_name, [])
    
    def get_sdk_summary(self) -> str:
        """Get a summary of the entire SDK."""
        summary_lines = []
        summary_lines.append("# SDK Summary")
        summary_lines.append("")
        
        for module_name, functions in self.modules.items():
            if functions:
                summary_lines.append(f"## {module_name.title()} Module ({len(functions)} functions)")
                for func in functions:
                    func_name = func.get('name', 'unknown')
                    func_summary = func.get('summary', 'No description')
                    summary_lines.append(f"- {func_name}: {func_summary}")
                summary_lines.append("")
        
        return '\n'.join(summary_lines)
    
    def cleanup_unused_functions(self, active_scenarios: List[str]) -> None:
        """Remove functions that are no longer used."""
        # This would implement cleanup logic
        # For now, we'll keep all functions
        pass
    
    def validate_sdk_integrity(self) -> bool:
        """Validate the integrity of the modular SDK."""
        try:
            # Check that all modules have valid structure
            for module_name, functions in self.modules.items():
                if not functions:
                    continue
                
                # Validate each function
                for func in functions:
                    if not func.get('name') or not func.get('content'):
                        logger.warning(f"Invalid function in module {module_name}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"SDK validation failed: {e}")
            return False
