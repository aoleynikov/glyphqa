from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
import json


@dataclass
class SdkFunction:
    """Represents a single SDK function with metadata."""
    
    name: str
    content: str  # The actual JavaScript function code
    summary: str  # Brief description of what this function does
    origin_scenario: str  # The scenario that originally created this function
    function_type: str  # 'action', 'check', 'teardown', 'utility'
    dependencies: List[str] = field(default_factory=list)  # Other SDK functions this depends on
    used_by: Set[str] = field(default_factory=set)  # Scenarios that use this function
    file_path: str = ""  # Path to the individual function file
    
    # Additional metadata fields
    purpose: str = ""  # What this function is designed to do
    parameters: List[Dict[str, str]] = field(default_factory=list)  # Parameter descriptions
    return_value: str = ""  # What this function returns
    complexity: str = ""  # 'simple', 'medium', 'complex'
    selectors_used: List[str] = field(default_factory=list)  # CSS selectors used in the function
    playwright_methods: List[str] = field(default_factory=list)  # Playwright methods used
    error_handling: bool = False  # Whether function includes error handling
    wait_strategies: List[str] = field(default_factory=list)  # Wait strategies used
    tags: List[str] = field(default_factory=list)  # Tags for categorization
    
    def __post_init__(self):
        """No auto-generation - all metadata should come from LLM analysis."""
        pass
    
    
    @classmethod
    def from_pure_js(cls, js_content: str, origin_scenario: str, function_name: str = None) -> 'SdkFunction':
        """Create SdkFunction from pure JavaScript content (metadata will be filled by LLM analysis)."""
        # Extract function name from JS content if not provided
        if not function_name:
            function_name = cls._extract_function_name_from_js(js_content)
        
        return cls(
            name=function_name,
            content=js_content,
            summary="",  # Will be filled by LLM analysis
            origin_scenario=origin_scenario,
            function_type="",  # Will be filled by LLM analysis
            purpose="",
            parameters=[],
            return_value="",
            complexity="",
            selectors_used=[],
            playwright_methods=[],
            error_handling=False,
            wait_strategies=[],
            tags=[]
        )
    
    @staticmethod
    def _extract_function_name_from_js(js_content: str) -> str:
        """Extract function name from JavaScript content."""
        import re
        # Look for function declaration patterns
        patterns = [
            r'(?:async\s+)?function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?\(',
            r'let\s+(\w+)\s*=\s*(?:async\s+)?\(',
            r'var\s+(\w+)\s*=\s*(?:async\s+)?\('
        ]
        
        for pattern in patterns:
            match = re.search(pattern, js_content)
            if match:
                return match.group(1)
        
        return "unknown_function"
    
    def save_to_file(self, sdk_dir: Path) -> None:
        """Save function to individual file in SDK directory organized by scenario."""
        scenario_dir = sdk_dir / self.origin_scenario
        scenario_dir.mkdir(exist_ok=True)
        
        # Use our custom format: .sdkf (SDK Function) files
        file_path = scenario_dir / f"{self.name}.sdkf"
        
        # Create the custom format content
        sdkf_content = self.to_sdkf_format()
        
        with open(file_path, 'w') as f:
            f.write(sdkf_content)
        
        self.file_path = str(file_path.relative_to(sdk_dir))
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'SdkFunction':
        """Load function from individual .sdkf file."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        return cls.from_sdkf_format(content, file_path)
    
    def to_sdkf_format(self) -> str:
        """Convert function to our custom .sdkf format using JSON."""
        # Create comprehensive metadata dictionary
        metadata = {
            "name": self.name,
            "type": self.function_type,
            "origin_scenario": self.origin_scenario,
            "summary": self.summary,
            "purpose": self.purpose,
            "parameters": self.parameters,
            "return_value": self.return_value,
            "complexity": self.complexity,
            "selectors_used": self.selectors_used,
            "playwright_methods": self.playwright_methods,
            "error_handling": self.error_handling,
            "wait_strategies": self.wait_strategies,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "used_by": list(self.used_by)
        }
        
        # Format as JSON with JavaScript function
        lines = []
        lines.append("// SDK Function Metadata (JSON)")
        lines.append(json.dumps(metadata, indent=2))
        lines.append("")
        lines.append("// JavaScript Function:")
        lines.append(self.content)
        
        return '\n'.join(lines)
    
    @classmethod
    def from_sdkf_format(cls, content: str, file_path: Path) -> 'SdkFunction':
        """Parse function from our custom .sdkf format using JSON."""
        lines = content.split('\n')
        
        # Find JSON metadata section
        json_start = -1
        json_end = -1
        js_start = -1
        
        for i, line in enumerate(lines):
            if line.strip() == "// SDK Function Metadata (JSON)":
                json_start = i + 1
            elif line.strip() == "// JavaScript Function:":
                js_start = i + 1
                if json_start != -1:
                    json_end = i
                break
        
        # Parse JSON metadata
        metadata = {}
        if json_start != -1 and json_end != -1:
            json_lines = lines[json_start:json_end]
            json_str = '\n'.join(json_lines)
            try:
                metadata = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON metadata in {file_path}: {e}")
        
        # Extract JavaScript function content
        js_content = ""
        if js_start != -1:
            js_lines = lines[js_start:]
            js_content = '\n'.join(js_lines)
        
        # Determine function type from file path if not in metadata
        function_type = metadata.get('type', cls._determine_function_type_from_path(file_path))
        
        return cls(
            name=metadata.get('name', file_path.stem),
            content=js_content,
            summary=metadata.get('summary', ''),
            origin_scenario=metadata.get('origin_scenario', ''),
            function_type=function_type,
            dependencies=metadata.get('dependencies', []),
            used_by=set(metadata.get('used_by', [])),
            file_path=str(file_path),
            purpose=metadata.get('purpose', ''),
            parameters=metadata.get('parameters', []),
            return_value=metadata.get('return_value', ''),
            complexity=metadata.get('complexity', ''),
            selectors_used=metadata.get('selectors_used', []),
            playwright_methods=metadata.get('playwright_methods', []),
            error_handling=metadata.get('error_handling', False),
            wait_strategies=metadata.get('wait_strategies', []),
            tags=metadata.get('tags', [])
        )
    
    @staticmethod
    def _determine_function_type_from_path(file_path: Path) -> str:
        """Fallback function type determination from file path (only used when metadata is missing)."""
        return "unknown"  # No heuristics - let LLM determine this
    
    def to_composable_js(self) -> str:
        """Convert function to composable JavaScript (without imports/exports)."""
        import re
        
        # Clean up the JavaScript content
        content = self.content.strip()
        
        # Remove any import/export statements
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if (line.startswith('import ') or 
                line.startswith('export ') or 
                'module.exports' in line or
                (line.startswith('const ') and 'require(' in line)):
                continue
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Fix SDK self-references - remove sdk. prefix when functions are composed into SDK
        content = re.sub(r'await sdk\.(\w+)\(', r'await \1(', content)
        content = re.sub(r'sdk\.(\w+)\(', r'\1(', content)
        
        # Fix common syntax issues
        # Remove extra closing braces
        content = re.sub(r'}\s*}\s*$', '}', content)
        content = re.sub(r'}\s*}\s*\n', '}\n', content)
        
        # Ensure proper function structure
        if 'async function' in content and not content.strip().endswith('}'):
            content = content.rstrip() + '\n}'
        
        return content
    
    def update_metadata_from_analysis(self, analysis_result: Dict[str, Any]) -> None:
        """Update function metadata from LLM analysis result."""
        self.summary = analysis_result.get('summary', self.summary)
        self.function_type = analysis_result.get('function_type', self.function_type)
        self.purpose = analysis_result.get('purpose', self.purpose)
        self.parameters = analysis_result.get('parameters', self.parameters)
        self.return_value = analysis_result.get('return_value', self.return_value)
        self.complexity = analysis_result.get('complexity', self.complexity)
        self.selectors_used = analysis_result.get('selectors_used', self.selectors_used)
        self.playwright_methods = analysis_result.get('playwright_methods', self.playwright_methods)
        self.error_handling = analysis_result.get('error_handling', self.error_handling)
        self.wait_strategies = analysis_result.get('wait_strategies', self.wait_strategies)
        self.tags = analysis_result.get('tags', self.tags)
        self.dependencies = analysis_result.get('dependencies', self.dependencies)
    
    def __repr__(self) -> str:
        """String representation for debugging and LLM context."""
        return f"{self.name}({self.function_type}): {self.summary}"
    
    def to_sdk_catalog_entry(self) -> str:
        """Create a catalog entry for this function."""
        return f"- **{self.name}** ({self.function_type}): {self.summary}"


class SdkManager:
    """Manages the modular SDK system."""
    
    def __init__(self, sdk_dir: Path):
        self.sdk_dir = Path(sdk_dir)
        self.functions: Dict[str, SdkFunction] = {}
        self.sdk_dir.mkdir(parents=True, exist_ok=True)
        self._load_existing_functions()
    
    def _load_existing_functions(self) -> None:
        """Load existing functions from the SDK directory."""
        if not self.sdk_dir.exists():
            return
        
        for scenario_dir in self.sdk_dir.iterdir():
            if scenario_dir.is_dir():
                for sdkf_file in scenario_dir.glob("*.sdkf"):
                    try:
                        func = SdkFunction.load_from_file(sdkf_file)
                        self.functions[func.name] = func
                    except Exception as e:
                        print(f"Warning: Failed to load {sdkf_file}: {e}")
    
    def _determine_function_type(self, function_name: str) -> str:
        """Determine function type from function name - now uses LLM analysis."""
        # This method is now deprecated - function type is determined by LLM analysis
        # in the analyze_function_with_llm method using the sdk_function_analyzer.j2 template
        return "unknown"  # Let LLM determine this
    
    def add_function(self, func: SdkFunction) -> None:
        """Add or update an SDK function."""
        self.functions[func.name] = func
        # Ensure the SDK directory exists
        self.sdk_dir.mkdir(exist_ok=True)
        func.save_to_file(self.sdk_dir)
    
    def get_function(self, name: str) -> Optional[SdkFunction]:
        """Get an SDK function by name."""
        return self.functions.get(name)
    
    def function_exists(self, name: str) -> bool:
        """Check if a function exists in the SDK."""
        return name in self.functions
    
    def get_functions_by_type(self, function_type: str) -> List[SdkFunction]:
        """Get all functions of a specific type."""
        return [func for func in self.functions.values() if func.function_type == function_type]
    
    def get_functions_by_origin_scenario(self, scenario_name: str) -> List[SdkFunction]:
        """Get all functions from a specific scenario."""
        return [func for func in self.functions.values() if func.origin_scenario == scenario_name]
    
    def get_functions_used_by_scenario(self, scenario_name: str) -> List[SdkFunction]:
        """Get all functions used by a specific scenario."""
        return [func for func in self.functions.values() if scenario_name in func.used_by]
    
    def compose_sdk_js(self, scenario_name: str = None, template_manager=None) -> str:
        """Compose a complete SDK JavaScript file from individual functions using a template."""
        if scenario_name:
            # Only include functions used by this scenario and their dependencies
            used_functions = self._get_functions_with_dependencies(scenario_name)
        else:
            # Include all functions
            used_functions = list(self.functions.values())
        
        # Sort functions by name for consistent output
        used_functions.sort(key=lambda f: f.name)
        
        if template_manager:
            # Use template to compose the SDK
            return template_manager.render_template(
                'targets/playwright/sdk_composer.j2',
                functions=used_functions
            )
        else:
            # Fallback to simple composition if no template manager
            composed_lines = []
            composed_lines.append("import { test, expect } from '@playwright/test';")
            composed_lines.append("")
            
            for func in used_functions:
                composed_lines.append(f"// {func.name} ({func.function_type})")
                composed_lines.append(func.to_composable_js())
                composed_lines.append("")
            
            composed_lines.append("export {")
            for func in used_functions:
                composed_lines.append(f"    {func.name},")
            composed_lines.append("};")
            
            return '\n'.join(composed_lines)
    
    def _get_functions_with_dependencies(self, scenario_name: str) -> List[SdkFunction]:
        """Get all functions used by a scenario plus their dependencies."""
        used_functions = []
        to_process = []
        
        # Start with functions used by the scenario
        for func in self.functions.values():
            if scenario_name in func.used_by:
                to_process.append(func.name)
        
        # Process dependencies
        while to_process:
            func_name = to_process.pop(0)
            if func_name in self.functions and func_name not in [f.name for f in used_functions]:
                func = self.functions[func_name]
                used_functions.append(func)
                # Add dependencies to processing queue
                for dep in func.dependencies:
                    if dep not in to_process:
                        to_process.append(dep)
        
        return used_functions
    
    def get_all_function_names(self) -> List[str]:
        """Get all function names in the SDK."""
        return list(self.functions.keys())
    
    def cleanup_unused_functions(self, active_scenarios: List[str]) -> None:
        """Remove functions that are no longer used by any active scenario."""
        to_remove = []
        
        for func in self.functions.values():
            if not func.used_by.intersection(set(active_scenarios)):
                to_remove.append(func.name)
        
        for func_name in to_remove:
            del self.functions[func_name]
            # Also remove the file
            func = self.functions.get(func_name)
            if func and func.file_path:
                file_path = self.sdk_dir / func.file_path
                if file_path.exists():
                    file_path.unlink()
    
    def generate_sdk_catalog(self) -> str:
        """Generate a catalog of all SDK functions."""
        catalog_lines = []
        catalog_lines.append("# SDK Function Catalog")
        catalog_lines.append("")
        
        # Group by type
        for func_type in ['action', 'check', 'teardown', 'utility']:
            functions = self.get_functions_by_type(func_type)
            if functions:
                catalog_lines.append(f"## {func_type.title()} Functions")
                catalog_lines.append("")
                for func in sorted(functions, key=lambda f: f.name):
                    catalog_lines.append(func.to_sdk_catalog_entry())
                catalog_lines.append("")
        
        return '\n'.join(catalog_lines)
    
    def get_functions_summary(self) -> str:
        """Get a summary of all functions for LLM context."""
        summary_lines = []
        for func in sorted(self.functions.values(), key=lambda f: f.name):
            summary_lines.append(f"- {func.name} ({func.function_type}): {func.summary}")
        return '\n'.join(summary_lines)
    
    def analyze_function_with_llm(self, func: SdkFunction, llm_provider, template_manager) -> SdkFunction:
        """Analyze a function using LLM to extract metadata."""
        try:
            # Use the function analyzer template
            system_prompt = template_manager.render_template(
                'sdk_function_analyzer.j2',
                function_content=func.content
            )
            
            # Get LLM analysis
            response = llm_provider.generate(system_prompt, "")
            
            # Parse JSON response
            import json
            analysis_result = json.loads(response)
            
            # Update function metadata
            func.update_metadata_from_analysis(analysis_result)
            
            return func
            
        except Exception as e:
            print(f"Warning: Failed to analyze function {func.name} with LLM: {e}")
            # Return function with minimal metadata
            return func