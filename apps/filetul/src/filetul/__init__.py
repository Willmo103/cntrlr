"""
Filetul: A tool for managing and organizing files and directories.
This module provides the core functionality for loading and managing target directories.
"""

from core.base import BaseDirectory


def load_target(target: str) -> BaseDirectory:
    """Load the target directory based on the provided path."""
    try:
        return BaseDirectory.populate(target)
    except Exception as e:
        raise ValueError(f"Failed to load target directory: {e}")
