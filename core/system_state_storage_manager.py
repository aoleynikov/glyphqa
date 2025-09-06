#!/usr/bin/env python3

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SystemStateStorageManager:
    """Storage manager for glyph.md system state operations."""
    
    def __init__(self, glyph_dir: Path, template_manager=None):
        self.glyph_dir = Path(glyph_dir)
        self.glyph_md_file = self.glyph_dir / "glyph.md"
        self.template_manager = template_manager
        self._ensure_glyph_dir_exists()
    
    def _ensure_glyph_dir_exists(self):
        """Ensure the .glyph directory exists."""
        self.glyph_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_content(self) -> str:
        """Get current glyph.md content, creating initial content if it doesn't exist."""
        if self.glyph_md_file.exists():
            return self.glyph_md_file.read_text()
        else:
            return self._get_initial_content()
    
    def _get_initial_content(self) -> str:
        """Get initial glyph.md content."""
        return self.template_manager.render_template('system_state/initial_content.j2', 
                                                  timestamp=datetime.now().isoformat())
    
    def write_content(self, content: str):
        """Write content to glyph.md."""
        self.glyph_md_file.write_text(content)
        logger.debug(f"Updated glyph.md with {len(content)} characters")
    
    def update_content(self, new_content: str):
        """Update glyph.md with new content."""
        self.write_content(new_content)
        logger.info(f"Updated glyph.md with new content")
    
    def reset_to_initial(self):
        """Reset glyph.md to initial state."""
        initial_content = self._get_initial_content()
        self.write_content(initial_content)
        logger.info("Reset glyph.md to initial state")
    
    def delete_if_exists(self):
        """Delete glyph.md if it exists."""
        if self.glyph_md_file.exists():
            self.glyph_md_file.unlink()
            logger.debug(f"Deleted glyph.md: {self.glyph_md_file}")
    
    def exists(self) -> bool:
        """Check if glyph.md exists."""
        return self.glyph_md_file.exists()
    
    def get_file_path(self) -> Path:
        """Get the path to glyph.md."""
        return self.glyph_md_file
