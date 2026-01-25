"""
Core configuration package.

This package contains modules for managing application configuration,
including environment detection, settings factories, and specific
configuration classes for various components of the application.

It leverages Pydantic for settings management, supporting multiple
sources such as environment variables and YAML files.
"""

from . import constants  # noqa: F401
from .config import (
    AppSettings,
    AuthSettings,  # noqa: F401
    ClipboardWatcherSettings,
    CliSettings,
    ControllerAPISettings,
    ConverterAPISettings,
    DatabaseSettings,
    GotifySettings,
    MQTTSettings,
    RedditSettings,
    S3Settings,
    STTSettings,
    TTSServerSettings,
    UiServerSettings,
    get_settings,
)
