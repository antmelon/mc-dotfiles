"""Cleanup script for the MCS application."""

import os
import shutil
from pathlib import Path

def remove_pycache(directory: str) -> None:
    """Remove __pycache__ directories and .pyc files."""
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))
            dirs.remove("__pycache__")
        
        # Remove .pyc files
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))

def main() -> None:
    """Run the cleanup process."""
    project_root = Path(__file__).parent
    remove_pycache(str(project_root))
    print("Cleanup complete!")

if __name__ == "__main__":
    main()
