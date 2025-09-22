"""
SDK Data Aggregator - Gathers and summarizes SDK data for build processes
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from .generic_modular_sdk_manager import GenericModularSdkManager

logger = logging.getLogger(__name__)

@dataclass
class SdkFunctionInfo:
    """Information about a single SDK function."""
    name: str
    module: str
    content: str
    summary: str
    function_type: str
    dependencies: List[str]
    parameters: List[Dict[str, str]]
    return_value: str
    complexity: str
    selectors_used: List[str]
    playwright_methods: List[str]

@dataclass
class SdkBuildContext:
    """Context information for SDK usage in builds."""
    available_functions: List[SdkFunctionInfo]
    function_imports: str
    function_catalog: str
    module_structure: Dict[str, List[str]]
    dependencies: Dict[str, List[str]]
    usage_examples: Dict[str, str]

class SdkDataAggregator:
    """
    Aggregates and summarizes SDK data for build processes.
    
    Responsibilities:
    - Gather all SDK functions from modules
    - Provide build context with correct imports
    - Generate usage examples and documentation
    - Handle function dependencies and relationships
    - Optimize SDK data for LLM context
    """
    
    def __init__(self, modular_sdk_manager: GenericModularSdkManager):
        self.sdk_manager = modular_sdk_manager
        self._cache = {}
        self._last_updated = None
    
    def get_build_context(self, scenario_name: str = None, 
                         target_functions: List[str] = None) -> SdkBuildContext:
        """
        Get SDK context optimized for a specific build scenario.
        
        Args:
            scenario_name: Name of the scenario being built
            target_functions: Specific functions needed for this build
            
        Returns:
            SdkBuildContext: Optimized SDK context for the build
        """
        
        # Check cache first
        cache_key = f"{scenario_name}_{target_functions}"
        if cache_key in self._cache and self._is_cache_valid():
            return self._cache[cache_key]
        
        # Gather SDK data
        available_functions = self._gather_functions(scenario_name, target_functions)
        function_imports = self._generate_imports(available_functions)
        function_catalog = self._generate_catalog(available_functions)
        module_structure = self._get_module_structure()
        dependencies = self._analyze_dependencies(available_functions)
        usage_examples = self._generate_usage_examples(available_functions)
        
        # Create build context
        context = SdkBuildContext(
            available_functions=available_functions,
            function_imports=function_imports,
            function_catalog=function_catalog,
            module_structure=module_structure,
            dependencies=dependencies,
            usage_examples=usage_examples
        )
        
        # Cache the result
        self._cache[cache_key] = context
        self._last_updated = self._get_sdk_timestamp()
        
        return context
    
    def _gather_functions(self, scenario_name: str = None, 
                         target_functions: List[str] = None) -> List[SdkFunctionInfo]:
        """Gather relevant functions for the build context."""
        
        all_functions = []
        
        # Get functions from all modules
        for module_name, functions in self.sdk_manager.modules.items():
            for func_data in functions:
                # Filter by target functions if specified
                if target_functions and func_data.get('name') not in target_functions:
                    continue
                
                # Create function info
                func_info = SdkFunctionInfo(
                    name=func_data.get('name', ''),
                    module=module_name,
                    content=func_data.get('content', ''),
                    summary=func_data.get('summary', ''),
                    function_type=func_data.get('type', ''),
                    dependencies=func_data.get('dependencies', []),
                    parameters=func_data.get('parameters', []),
                    return_value=func_data.get('return_value', ''),
                    complexity=func_data.get('complexity', ''),
                    selectors_used=func_data.get('selectors_used', []),
                    playwright_methods=func_data.get('playwright_methods', [])
                )
                
                all_functions.append(func_info)
        
        return all_functions
    
    def _generate_imports(self, functions: List[SdkFunctionInfo]) -> str:
        """Generate import statements for the functions."""
        
        if not functions:
            return "// No SDK functions available"
        
        # Group by module
        module_functions = {}
        for func in functions:
            if func.module not in module_functions:
                module_functions[func.module] = []
            module_functions[func.module].append(func.name)
        
        # Generate imports
        import_lines = []
        import_lines.append("// SDK Function Imports")
        import_lines.append("")
        
        for module_name, func_names in module_functions.items():
            if func_names:
                func_list = ", ".join(func_names)
                import_lines.append(f"import {{ {func_list} }} from './modules/{module_name}/index.js';")
        
        return "\n".join(import_lines)
    
    def _generate_catalog(self, functions: List[SdkFunctionInfo]) -> str:
        """Generate a catalog of available functions."""
        
        if not functions:
            return "// No SDK functions available"
        
        catalog_lines = []
        catalog_lines.append("// Available SDK Functions:")
        catalog_lines.append("")
        
        # Group by module
        module_functions = {}
        for func in functions:
            if func.module not in module_functions:
                module_functions[func.module] = []
            module_functions[func.module].append(func)
        
        # Generate catalog
        for module_name, module_functions in module_functions.items():
            catalog_lines.append(f"// {module_name.upper()} MODULE:")
            for func in module_functions:
                catalog_lines.append(f"// - {func.name}: {func.summary}")
            catalog_lines.append("")
        
        return "\n".join(catalog_lines)
    
    def _get_module_structure(self) -> Dict[str, List[str]]:
        """Get the current module structure."""
        structure = {}
        
        for module_name, functions in self.sdk_manager.modules.items():
            structure[module_name] = [func.get('name', '') for func in functions]
        
        return structure
    
    def _analyze_dependencies(self, functions: List[SdkFunctionInfo]) -> Dict[str, List[str]]:
        """Analyze function dependencies."""
        dependencies = {}
        
        for func in functions:
            func_deps = []
            for dep in func.dependencies:
                # Check if dependency exists in available functions
                if any(f.name == dep for f in functions):
                    func_deps.append(dep)
            
            if func_deps:
                dependencies[func.name] = func_deps
        
        return dependencies
    
    def _generate_usage_examples(self, functions: List[SdkFunctionInfo]) -> Dict[str, str]:
        """Generate usage examples for functions."""
        examples = {}
        
        for func in functions:
            # Generate example based on function type and parameters
            example = self._create_usage_example(func)
            examples[func.name] = example
        
        return examples
    
    def _create_usage_example(self, func: SdkFunctionInfo) -> str:
        """Create a usage example for a function."""
        
        # Basic usage pattern
        if func.parameters:
            param_list = ", ".join([p.get('name', 'param') for p in func.parameters])
            example = f"await {func.name}({param_list});"
        else:
            example = f"await {func.name}();"
        
        return example
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if not self._last_updated:
            return False
        
        current_timestamp = self._get_sdk_timestamp()
        return current_timestamp == self._last_updated
    
    def _get_sdk_timestamp(self) -> str:
        """Get timestamp of SDK last modification."""
        # This would check file modification times
        # For now, return a simple timestamp
        return "unknown"
    
    def get_function_by_name(self, function_name: str) -> Optional[SdkFunctionInfo]:
        """Get a specific function by name."""
        for module_name, functions in self.sdk_manager.modules.items():
            for func_data in functions:
                if func_data.get('name') == function_name:
                    return SdkFunctionInfo(
                        name=func_data.get('name', ''),
                        module=module_name,
                        content=func_data.get('content', ''),
                        summary=func_data.get('summary', ''),
                        function_type=func_data.get('type', ''),
                        dependencies=func_data.get('dependencies', []),
                        parameters=func_data.get('parameters', []),
                        return_value=func_data.get('return_value', ''),
                        complexity=func_data.get('complexity', ''),
                        selectors_used=func_data.get('selectors_used', []),
                        playwright_methods=func_data.get('playwright_methods', [])
                    )
        
        return None
    
    def get_functions_by_module(self, module_name: str) -> List[SdkFunctionInfo]:
        """Get all functions in a specific module."""
        functions = []
        
        if module_name in self.sdk_manager.modules:
            for func_data in self.sdk_manager.modules[module_name]:
                func_info = SdkFunctionInfo(
                    name=func_data.get('name', ''),
                    module=module_name,
                    content=func_data.get('content', ''),
                    summary=func_data.get('summary', ''),
                    function_type=func_data.get('type', ''),
                    dependencies=func_data.get('dependencies', []),
                    parameters=func_data.get('parameters', []),
                    return_value=func_data.get('return_value', ''),
                    complexity=func_data.get('complexity', ''),
                    selectors_used=func_data.get('selectors_used', []),
                    playwright_methods=func_data.get('playwright_methods', [])
                )
                functions.append(func_info)
        
        return functions
    
    def clear_cache(self) -> None:
        """Clear the function cache."""
        self._cache.clear()
        self._last_updated = None
    
    def get_sdk_summary_for_llm(self, max_functions: int = 20) -> str:
        """Get a concise summary of SDK functions for LLM context."""
        
        all_functions = self._gather_functions()
        
        # Limit functions to avoid context overflow
        if len(all_functions) > max_functions:
            all_functions = all_functions[:max_functions]
        
        summary_lines = []
        summary_lines.append("Available SDK Functions:")
        summary_lines.append("")
        
        for func in all_functions:
            summary_lines.append(f"- {func.name} ({func.module}): {func.summary}")
        
        return "\n".join(summary_lines)
