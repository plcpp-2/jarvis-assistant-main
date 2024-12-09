import os
import shutil
from typing import List, Optional
from pathlib import Path

class FileOperations:
    def __init__(self, base_directory: Optional[str] = None):
        self.base_directory = Path(base_directory) if base_directory else Path.home()

    def create_directory(self, directory_path: str) -> bool:
        """Create a new directory."""
        try:
            full_path = self.base_directory / directory_path
            full_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False

    def list_directory(self, directory_path: str = ".") -> List[str]:
        """List contents of a directory."""
        try:
            full_path = self.base_directory / directory_path
            return [str(item.relative_to(full_path)) for item in full_path.iterdir()]
        except Exception as e:
            print(f"Error listing directory: {e}")
            return []

    def move_file(self, source: str, destination: str) -> bool:
        """Move a file from source to destination."""
        try:
            src_path = self.base_directory / source
            dest_path = self.base_directory / destination
            shutil.move(str(src_path), str(dest_path))
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False

    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            full_path = self.base_directory / file_path
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(str(full_path))
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
