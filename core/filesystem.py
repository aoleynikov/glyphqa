from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class FileSystem:
    """Wrapper for file system operations to make testing easier."""
    
    def __init__(self):
        pass
    
    def exists(self, path: str) -> bool:
        """Check if a file or directory exists."""
        return Path(path).exists()
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        return Path(path).is_dir()
    
    def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """Read text from a file."""
        return Path(path).read_text(encoding=encoding)
    
    def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> None:
        """Write text to a file."""
        Path(path).write_text(content, encoding=encoding)
    
    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)
    
    def glob(self, pattern: str) -> List[str]:
        """Find files matching a pattern."""
        return [str(p) for p in Path('.').glob(pattern)]
    
    def unlink(self, path: str) -> None:
        """Remove a file."""
        Path(path).unlink()
    
    def get_stem(self, path: str) -> str:
        """Get the stem (filename without extension) of a path."""
        return Path(path).stem
    
    def get_name(self, path: str) -> str:
        """Get the name (filename with extension) of a path."""
        return Path(path).name
