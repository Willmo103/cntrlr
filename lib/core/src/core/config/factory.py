# region Docstring
"""
core.config.factory
Factory module for creating and managing application settings with multi-source configuration support.
Overview:
- Provides a custom Pydantic BaseSettings subclass that supports hierarchical configuration
    loading from multiple sources including YAML files, environment variables, and .env files.
- Implements a cached factory function for efficient settings instantiation across the application.
Contents:
- Constants:
    - T: TypeVar bound to BaseSettings for generic typing support in the factory function.
- Classes:
    - FactoryBaseSettings:
        Custom BaseSettings subclass that extends Pydantic's configuration capabilities to support
        YAML configuration files alongside standard environment variable loading. Implements a
        priority-based configuration resolution system.
        Configuration Priority (highest to lowest):
            1. Environment variables
            2. .env file values
            3. YAML files (environment-specific config.{env}.yaml)
            4. YAML files (default config.yaml)
            5. Field defaults
        Key Features:
            - Automatic loading of config.yaml and config.{APP_ENV}.yaml from APP_ROOT
            - Graceful handling of non-JSON values in .env files (e.g., CORS='*')
            - UTF-8 encoded .env file support
            - Extra fields are ignored to prevent validation errors from unknown config keys
- Functions:
    - get_settings(settings_cls: Type[T]) -> T:
        LRU-cached factory function that instantiates and returns settings objects. Caching
        ensures configuration files are only read once per settings class, improving performance
        for frequently accessed configuration values.
Design notes:
- The settings_customise_sources method overrides Pydantic's default source chain to inject
    YAML configuration support while maintaining compatibility with standard env/dotenv loading.
- The decode_complex_value method provides fault-tolerant parsing of complex values, returning
    raw strings when JSON decoding fails rather than raising exceptions.
- LRU caching on get_settings prevents redundant file I/O and parsing when the same settings
    class is requested multiple times during application lifecycle.
"""

# region Imports
import json
from functools import lru_cache
from typing import Any, Type, TypeVar

from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .base import APP_ENV, APP_ROOT

# endregion
# region FactoryBaseSettings Class
T = TypeVar("T", bound=BaseSettings)


class FactoryBaseSettings(BaseSettings):
    """
    Custom BaseSettings that supports YAML and Env Vars.
    Priority: Env Vars > YAML (Env specific) > YAML (Default) > Defaults
    """

    model_config = SettingsConfigDict(
        env_file=APP_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:

        # Load config.yaml and config.{env}.yaml
        yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file=[APP_ROOT / "config.yaml", APP_ROOT / f"config.{APP_ENV}.yaml"],
        )
        return (
            env_settings,  # Environment variables (highest priority)
            dotenv_settings,  # .env file
            yaml_settings,  # YAML files
            init_settings,  # Init kwargs
        )

    def decode_complex_value(
        self, field_name: str, field: FieldInfo, value: Any
    ) -> Any:
        """
        Overridden to prevent crashes when .env contains non-JSON lists (like CORS '*').
        If JSON decoding fails, return the raw string so the validator can handle it.
        """
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # This is the key fix: Return the raw string if it's not JSON
                return value
        return value


# endregion
# region get_settings Factory Function


@lru_cache
def get_settings(settings_cls: Type[T]) -> T:
    """
    Factory function to load any settings class.
    Results are cached so we don't re-read files every time.
    """
    return settings_cls()


# endregion
