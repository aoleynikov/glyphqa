"""
SDK Maintenance Agent - Handles all SDK operations and maintenance.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .sdk_function import SdkManager, SdkFunction

logger = logging.getLogger(__name__)


@dataclass
class SdkUpdateRequest:
    """Request to update the SDK with a new scenario function."""
    scenario_name: str
    function_name: str
    function_content: str
    function_type: str = "scenario"
    summary: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.summary is None:
            self.summary = f"Complete scenario implementation for {self.scenario_name}"


@dataclass
class SdkInfo:
    """Information about available SDK functions."""
    available_functions: List[str]
    function_metadata: Dict[str, Dict[str, Any]]
    sdk_file_path: str
    last_updated: str


class SdkAgent:
    """
    Dedicated agent for SDK maintenance and management.
    
    Responsibilities:
    - Add new functions to the SDK
    - Maintain SDK integrity and consistency
    - Provide SDK information to other agents
    - Handle SDK composition and file management
    - Manage function dependencies and relationships
    """
    
    def __init__(self, sdk_manager: SdkManager, template_manager, filesystem):
        self.sdk_manager = sdk_manager
        self.template_manager = template_manager
        self.filesystem = filesystem
        self.sdk_file_path = '.glyph/sdk.js'
        
    def add_scenario_function(self, request: SdkUpdateRequest) -> bool:
        """
        Add a new scenario function to the SDK.
        
        Args:
            request: SdkUpdateRequest with function details
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        logger.info(f"Adding scenario function '{request.function_name}' to SDK")
        
        # Create SDK function object
        sdk_function = SdkFunction(
            name=request.function_name,
            content=request.function_content,
            summary=request.summary,
            origin_scenario=request.scenario_name,
            function_type=request.function_type,
            dependencies=request.dependencies
        )
        
        # Add to SDK manager
        self.sdk_manager.add_function(sdk_function)
        
        # Compose and save the updated SDK
        self._compose_and_save_sdk()
        
        logger.info(f"✅ Successfully added '{request.function_name}' to SDK")
        return True
    
    def get_sdk_info(self) -> SdkInfo:
        """
        Get comprehensive information about the current SDK state.
        
        Returns:
            SdkInfo: Current SDK information
        """
        try:
            available_functions = list(self.sdk_manager.functions.keys())
            
            function_metadata = {}
            for name, func in self.sdk_manager.functions.items():
                function_metadata[name] = {
                    'type': func.function_type,
                    'summary': func.summary,
                    'origin_scenario': func.origin_scenario,
                    'dependencies': func.dependencies,
                    'used_by': func.used_by
                }
            
            # Get last updated timestamp
            last_updated = "unknown"
            if self.filesystem.exists(self.sdk_file_path):
                # In a real implementation, you'd get file modification time
                last_updated = "recent"
            
            return SdkInfo(
                available_functions=available_functions,
                function_metadata=function_metadata,
                sdk_file_path=self.sdk_file_path,
                last_updated=last_updated
            )
            
        except Exception as e:
            logger.error(f"Failed to get SDK info: {e}")
            return SdkInfo(
                available_functions=[],
                function_metadata={},
                sdk_file_path=self.sdk_file_path,
                last_updated="error"
            )
    
    def get_available_functions(self) -> List[str]:
        """
        Get list of available function names in the SDK.
        
        Returns:
            List[str]: Available function names
        """
        return list(self.sdk_manager.functions.keys())
    
    def get_function_dependencies(self, function_name: str) -> List[str]:
        """
        Get dependencies for a specific function.
        
        Args:
            function_name: Name of the function
            
        Returns:
            List[str]: List of dependency function names
        """
        if function_name in self.sdk_manager.functions:
            return self.sdk_manager.functions[function_name].dependencies
        return []
    
    def is_function_available(self, function_name: str) -> bool:
        """
        Check if a function is available in the SDK.
        
        Args:
            function_name: Name of the function to check
            
        Returns:
            bool: True if function exists, False otherwise
        """
        return function_name in self.sdk_manager.functions
    
    def validate_sdk_integrity(self) -> bool:
        """
        Validate that the SDK is in a consistent state.
        
        Returns:
            bool: True if SDK is valid, False otherwise
        """
        try:
            # Check if SDK file exists and is readable
            if not self.filesystem.exists(self.sdk_file_path):
                logger.warning("SDK file does not exist")
                return False
            
            # Try to read the SDK file
            sdk_content = self.filesystem.read_text(self.sdk_file_path)
            
            # Basic syntax validation (check for export statement)
            if 'export {' not in sdk_content:
                logger.warning("SDK file missing export statement")
                return False
            
            # Check for malformed exports
            if sdk_content.count('export {') != sdk_content.count('};'):
                logger.warning("SDK file has malformed export statements")
                return False
            
            logger.info("✅ SDK integrity validation passed")
            return True
            
        except Exception as e:
            logger.error(f"SDK integrity validation failed: {e}")
            return False
    
    def rebuild_sdk(self) -> bool:
        """
        Rebuild the entire SDK from scratch.
        
        Returns:
            bool: True if rebuild successful, False otherwise
        """
        logger.info("Rebuilding SDK from scratch")
        self._compose_and_save_sdk()
        logger.info("✅ SDK rebuild completed successfully")
        return True
    
    def _compose_and_save_sdk(self):
        """Internal method to compose and save the SDK file."""
        # Compose the SDK using the template manager
        sdk_content = self.sdk_manager.compose_sdk_js(template_manager=self.template_manager)
        
        # Write to file
        self.filesystem.write_text(self.sdk_file_path, sdk_content)
        
        logger.debug(f"SDK composed and saved to {self.sdk_file_path}")
    
    def get_sdk_for_scenario(self, scenario_name: str) -> str:
        """
        Get SDK content optimized for a specific scenario.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            str: SDK content with only relevant functions
        """
        try:
            # Compose SDK with only functions used by this scenario
            sdk_content = self.sdk_manager.compose_sdk_js(
                scenario_name=scenario_name,
                template_manager=self.template_manager
            )
            return sdk_content
            
        except Exception as e:
            logger.error(f"Failed to get SDK for scenario {scenario_name}: {e}")
            # Fallback to full SDK
            return self.sdk_manager.compose_sdk_js(template_manager=self.template_manager)
    
    def cleanup_orphaned_functions(self) -> int:
        """
        Remove functions that are no longer referenced by any scenarios.
        
        Returns:
            int: Number of functions removed
        """
        try:
            removed_count = 0
            functions_to_remove = []
            
            for name, func in self.sdk_manager.functions.items():
                # Remove functions that are not used by any scenarios
                if not func.used_by and func.function_type == "scenario":
                    functions_to_remove.append(name)
            
            for name in functions_to_remove:
                del self.sdk_manager.functions[name]
                removed_count += 1
                logger.info(f"Removed orphaned function: {name}")
            
            if removed_count > 0:
                self._compose_and_save_sdk()
                logger.info(f"✅ Cleaned up {removed_count} orphaned functions")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned functions: {e}")
            return 0
