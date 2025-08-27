#!/usr/bin/env python3

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Guide:
    """Represents a built guide with hash information."""
    scenario_name: str
    actions: list
    glyph_hash: str
    built_at: str
    dependencies: list = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


def calculate_glyph_hash(glyph_file_path: str) -> str:
    """Calculate SHA256 hash of the glyph file content."""
    try:
        with open(glyph_file_path, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {glyph_file_path}: {e}")
        return ""


class HashCachingSystem:
    """Manages hash-based caching for scenario building."""
    
    def __init__(self, glyph_dir: Path):
        self.glyph_dir = Path(glyph_dir)
        self.guides_dir = self.glyph_dir / "guides"
        self.guides_dir.mkdir(parents=True, exist_ok=True)
    
    def should_rebuild_guide(self, scenario_name: str, glyph_file_path: str, force: bool = False) -> bool:
        """Check if guide needs rebuilding based on hash comparison."""
        
        if force:
            logger.info(f"🔄 Force rebuild requested for {scenario_name}")
            return True
        
        guide_file = self.guides_dir / f"{scenario_name}.guide"
        
        # If no guide exists, must build
        if not guide_file.exists():
            logger.info(f"📝 No guide found for {scenario_name}, building...")
            return True
        
        # Load existing guide
        try:
            with open(guide_file, 'r') as f:
                guide_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load guide for {scenario_name}: {e}")
            return True
        
        # Calculate current hash
        current_hash = calculate_glyph_hash(glyph_file_path)
        stored_hash = guide_data.get('glyph_hash', '')
        
        if not current_hash:
            logger.warning(f"Failed to calculate hash for {scenario_name}, rebuilding...")
            return True
        
        if current_hash != stored_hash:
            logger.info(f"🔄 Glyph file changed for {scenario_name}")
            logger.debug(f"   Old hash: {stored_hash[:8]}...")
            logger.debug(f"   New hash: {current_hash[:8]}...")
            return True
        
        logger.info(f"✅ Guide up to date for {scenario_name}")
        return False
    
    def save_guide(self, guide: Guide):
        """Save guide with hash to JSON file."""
        guide_file = self.guides_dir / f"{guide.scenario_name}.guide"
        
        guide_data = {
            "scenario_name": guide.scenario_name,
            "actions": guide.actions,
            "glyph_hash": guide.glyph_hash,
            "built_at": guide.built_at,
            "dependencies": guide.dependencies
        }
        
        try:
            with open(guide_file, 'w') as f:
                json.dump(guide_data, f, indent=2)
            logger.debug(f"Saved guide for {guide.scenario_name}")
        except Exception as e:
            logger.error(f"Failed to save guide for {guide.scenario_name}: {e}")
    
    def load_guide(self, scenario_name: str) -> Optional[Guide]:
        """Load guide from JSON file."""
        guide_file = self.guides_dir / f"{scenario_name}.guide"
        
        if not guide_file.exists():
            return None
        
        try:
            with open(guide_file, 'r') as f:
                data = json.load(f)
            
            return Guide(
                scenario_name=data['scenario_name'],
                actions=data['actions'],
                glyph_hash=data['glyph_hash'],
                built_at=data['built_at'],
                dependencies=data.get('dependencies', [])
            )
        except Exception as e:
            logger.error(f"Failed to load guide for {scenario_name}: {e}")
            return None
    
    def build_scenario_with_caching(self, scenario_name: str, glyph_file_path: str, force: bool = False) -> str:
        """Build scenario with caching, returning test function code."""
        
        # Check if rebuild is needed
        if self.should_rebuild_guide(scenario_name, glyph_file_path, force):
            logger.info(f"🔨 Building: {scenario_name}")
            
            # Build the guide (this would be the actual guide building logic)
            guide = self._build_guide(scenario_name, glyph_file_path)
            
            # Build the test function
            test_function = self._build_test_function(scenario_name, guide)
            
            # Run and learn (this would be the actual test execution)
            self._run_and_learn(test_function)
            
            # Save the guide
            self.save_guide(guide)
            
            logger.info(f"✅ Built and learned: {scenario_name}")
            return test_function
        else:
            # Load existing guide and test function
            guide = self.load_guide(scenario_name)
            if guide:
                test_function = self._load_existing_test_function(scenario_name)
                logger.info(f"📖 Using cached: {scenario_name}")
                return test_function
            else:
                logger.warning(f"Cache check passed but guide not found for {scenario_name}, rebuilding...")
                return self.build_scenario_with_caching(scenario_name, glyph_file_path, force=True)
    
    def _build_guide(self, scenario_name: str, glyph_file_path: str) -> Guide:
        """Build a guide from a glyph file."""
        # This is a placeholder - in real implementation, this would parse the glyph file
        # and generate the action list
        current_hash = calculate_glyph_hash(glyph_file_path)
        
        # Mock guide building - in real implementation, this would parse the .glyph file
        actions = [
            "navigate to login page",
            "type admin as username",
            "type admin_password as password",
            "click login button"
        ]
        
        return Guide(
            scenario_name=scenario_name,
            actions=actions,
            glyph_hash=current_hash,
            built_at=datetime.now().isoformat(),
            dependencies=[]
        )
    
    def _build_test_function(self, scenario_name: str, guide: Guide) -> str:
        """Build a test function from a guide."""
        # This is a placeholder - in real implementation, this would generate
        # actual Playwright test function code
        return f"// Test function for {scenario_name}"
    
    def _run_and_learn(self, test_function: str):
        """Run test and learn from results."""
        # This is a placeholder - in real implementation, this would execute
        # the test and update glyph.md with learned information
        logger.debug(f"Running and learning from test function")
    
    def _load_existing_test_function(self, scenario_name: str) -> str:
        """Load existing test function from cache."""
        # This is a placeholder - in real implementation, this would load
        # the cached test function code
        return f"// Cached test function for {scenario_name}"
    
    def purge_cached_knowledge(self):
        """Purge all cached knowledge by removing all guides and glyph.md."""
        logger.info("🧹 Purging all cached knowledge")
        
        # Remove all guide files
        guides_dir = self.guides_dir
        if guides_dir.exists():
            for guide_file in guides_dir.glob("*.guide"):
                guide_file.unlink()
                logger.debug(f"Removed guide: {guide_file}")
        
        # Reset glyph.md to initial state
        glyph_md_file = self.glyph_dir / "glyph.md"
        if glyph_md_file.exists():
            glyph_md_file.unlink()
            logger.debug(f"Removed glyph.md: {glyph_md_file}")
        
        # Create fresh glyph.md with initial structure
        initial_glyph_content = """# GlyphQA System Catalog
*Last updated: {datetime}*

## System Insights

## Pages Discovered

## Site Map

## Known Selectors

## Build Layers

## Common Failures & Solutions
"""
        
        glyph_md_file.write_text(initial_glyph_content.format(
            datetime=datetime.now().isoformat()
        ))
        logger.info("✅ Purge completed - system ready for fresh learning")
    
    def build_scenario_with_purge(self, scenario_name: str, glyph_file_path: str) -> str:
        """Build scenario with purge - removes all cached knowledge first."""
        logger.info(f"🔄 Purge build for {scenario_name}")
        
        # Perform purge
        self.purge_cached_knowledge()
        
        # Now build with no preexisting knowledge
        return self.build_scenario_with_caching(scenario_name, glyph_file_path, force=False)
