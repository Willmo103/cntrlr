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
from core.config import AppSettings, get_settings, ConverterAPISettings

app_settings: AppSettings = AppSettings()
"""Application-wide settings instance."""
api_settings: ConverterAPISettings = get_settings(ConverterAPISettings)
"""Converter API-specific settings instance: ('PORT', 'HOST', and 'LOG_LEVEL')."""
_storage = app_settings.app_root / "storage"

INPUT_STORAGE_PATH: Path = _storage / "input"
"""Path to the base input storage directory. (services create their own subdirectories here)"""
CONVERTED_STORAGE_PATH: Path = _storage / "converted"
"""Path to the base converted storage directory."""
