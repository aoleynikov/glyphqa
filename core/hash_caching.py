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


def calculate_glyph_hash(glyph_file_path: str, filesystem) -> str:
    """Calculate SHA256 hash of the glyph file content."""
    try:
        content = filesystem.read_text(glyph_file_path).encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {glyph_file_path}: {e}")
        return ""


class HashCachingSystem:
    """Manages hash-based caching for scenario building."""
    
    def __init__(self, glyph_dir: Path, filesystem=None):
        self.glyph_dir = Path(glyph_dir)
        self.filesystem = filesystem
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
            guide_content = self.filesystem.read_text(str(guide_file))
            guide_data = json.loads(guide_content)
        except Exception as e:
            logger.warning(f"Failed to load guide for {scenario_name}: {e}")
            return True
        
        # Calculate current hash
        current_hash = calculate_glyph_hash(glyph_file_path, self.filesystem)
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
            json_content = json.dumps(guide_data, indent=2)
            self.filesystem.write_text(str(guide_file), json_content)
            logger.debug(f"Saved guide for {guide.scenario_name}")
        except Exception as e:
            logger.error(f"Failed to save guide for {guide.scenario_name}: {e}")
    
    def load_guide(self, scenario_name: str) -> Optional[Guide]:
        """Load guide from JSON file."""
        guide_file = self.guides_dir / f"{scenario_name}.guide"
        
        if not guide_file.exists():
            return None
        
        try:
            guide_content = self.filesystem.read_text(str(guide_file))
            data = json.loads(guide_content)
            
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
    
    def build_scenario_with_caching(self, scenario_name: str, glyph_file_path: str, force: bool = False, builder_callback=None) -> str:
        """Build scenario with caching, returning test function code."""
        
        # Check if rebuild is needed
        if self.should_rebuild_guide(scenario_name, glyph_file_path, force):
            logger.info(f"🔨 Building: {scenario_name}")
            
            # Delegate actual building to the provided callback
            if builder_callback:
                guide = builder_callback(scenario_name, glyph_file_path)
                self.save_guide(guide)
                logger.info(f"✅ Built and cached: {scenario_name}")
                return guide
            else:
                logger.warning(f"No builder callback provided for {scenario_name}")
                return None
        else:
            # Load existing guide
            guide = self.load_guide(scenario_name)
            if guide:
                logger.info(f"📖 Using cached: {scenario_name}")
                return guide
            else:
                logger.warning(f"Cache check passed but guide not found for {scenario_name}, rebuilding...")
                return self.build_scenario_with_caching(scenario_name, glyph_file_path, force=True, builder_callback=builder_callback)
    

    
    def purge_cached_knowledge(self):
        """Purge all cached knowledge by removing all guides."""
        logger.info("🧹 Purging all cached knowledge")
        
        # Remove all guide files
        guides_dir = self.guides_dir
        if guides_dir.exists():
            for guide_file in guides_dir.glob("*.guide"):
                guide_file.unlink()
                logger.debug(f"Removed guide: {guide_file}")
        
        logger.info("✅ Purge completed - system ready for fresh learning")
    
    def build_scenario_with_purge(self, scenario_name: str, glyph_file_path: str, builder_callback=None) -> str:
        """Build scenario with purge - removes all cached knowledge first."""
        logger.info(f"🔄 Purge build for {scenario_name}")
        
        # Perform purge
        self.purge_cached_knowledge()
        
        # Now build with no preexisting knowledge
        return self.build_scenario_with_caching(scenario_name, glyph_file_path, force=False, builder_callback=builder_callback)
