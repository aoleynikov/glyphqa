from pathlib import Path
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class FileSystem:
    """Wrapper for file system operations to make testing easier."""
    
    def __init__(self):
        pass
    
    def exists(self, path: str) -> bool:
        """Check if a file or directory exists."""
        return Path(path).exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        return Path(path).is_file()
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        return Path(path).is_dir()
    
    def read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """Read text from a file."""
        return Path(path).read_text(encoding=encoding)
    
    def write_text(self, path: str, content: str, encoding: str = 'utf-8') -> None:
        """Write text to a file."""
        Path(path).write_text(content, encoding=encoding)
    
    def read_json(self, path: str) -> dict:
        """Read JSON from a file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def write_json(self, path: str, data: dict, indent: int = 2) -> None:
        """Write JSON to a file."""
        with open(path, 'w') as f:
            json.dump(data, f, indent=indent)
    
    def mkdir(self, path: str, parents: bool = False, exist_ok: bool = False) -> None:
        """Create a directory."""
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)
    
    def glob(self, pattern: str) -> List[str]:
        """Find files matching a pattern."""
        return [str(p) for p in Path('.').glob(pattern)]
    
    def rmtree(self, path: str) -> None:
        """Remove a directory tree."""
        import shutil
        shutil.rmtree(path)
    
    def copytree(self, src: str, dst: str) -> None:
        """Copy a directory tree."""
        import shutil
        shutil.copytree(src, dst)
    
    def unlink(self, path: str) -> None:
        """Remove a file."""
        Path(path).unlink()
    
    def get_stem(self, path: str) -> str:
        """Get the stem (filename without extension) of a path."""
        return Path(path).stem
    
    def get_name(self, path: str) -> str:
        """Get the name (filename with extension) of a path."""
        return Path(path).name
