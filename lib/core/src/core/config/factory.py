from functools import lru_cache
import json
from typing import Any, Type, TypeVar
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from pydantic.fields import FieldInfo
from .base import APP_ENV, APP_ROOT

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


@lru_cache
def get_settings(settings_cls: Type[T]) -> T:
    """
    Factory function to load any settings class.
    Results are cached so we don't re-read files every time.
    """
    return settings_cls()
