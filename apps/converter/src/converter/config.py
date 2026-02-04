"""
Configuration settings for the Converter application.

This module provides application and API settings instances,
as well as paths for input and converted data storage.

Attributes:
    app_settings: Application-wide settings instance.
    api_settings: Converter API-specific settings (PORT, HOST, LOG_LEVEL).
    INPUT_STORAGE_PATH: Path to the base input storage directory.
    CONVERTED_STORAGE_PATH: Path to the base converted storage directory.
"""

from pathlib import Path
from core.config import get_settings, ConverterAPISettings

app_root = Path(
    __file__
).parent.parent.parent.resolve()  # The root of the application directory stays local to the converter app for Docker and modularity.
"""The root directory of the Converter application."""


"""Application-wide settings instance."""
api_settings: ConverterAPISettings = get_settings(ConverterAPISettings)
"""Converter API-specific settings instance: ('PORT', 'HOST', and 'LOG_LEVEL')."""

# Create a tmp var for storage paths
# Ensure storage directories exist
_storage = app_root / "storage"
_storage.mkdir(parents=True, exist_ok=True)


INPUT_STORAGE_PATH: Path = _storage / "input"
"""Path to the base input storage directory. (services create their own subdirectories here)"""
CONVERTED_STORAGE_PATH: Path = _storage / "converted"
"""Path to the base converted storage directory."""

# Create storage directories if they do not exist
INPUT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
CONVERTED_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
