"""
core.config
Configuration and settings management for the Controller API application.
Overview:
- Provides Pydantic-based settings classes for all application services and components.
- Each settings class inherits from FactoryBaseSettings and supports environment variable
    overrides via Field aliases.
- Settings are organized by service/component for modular configuration management.
Contents:
- Imports:
    - Database: SQLite utility for CLI caching.
    - FactoryBaseSettings: Base settings class with factory pattern support.
    - get_settings: Factory function for retrieving settings instances (exported).
- Settings Classes:
    - ControllerAPISettings:
        Configuration for the main Controller API server including host, port, and log level.
    - OllamaSettings:
        Configuration for the Ollama LLM service including host, default model, context size,
        temperature, top_k, top_p, embedding model, and vision-language model settings.
    - ConverterAPISettings:
        Configuration for the Converter API server including host, port, and log level.
    - MQTTSettings:
        Configuration for MQTT broker connection including broker host, port, credentials,
        and topic prefix.
    - TTSServerSettings:
        Configuration for Piper TTS service including host, port, log level, model directory,
        output directory, default model, and speaker ID.
    - STTSettings:
        Configuration for Speech-to-Text service including sample rate, model size, log level,
        host, and port.
    - S3Settings:
        S3-compatible storage configuration including endpoint URL, credentials, bucket names,
        presigned URL timeout, and predefined bucket list for various content types.
    - UiServerSettings:
        Configuration for the UI server including host, port, log level, and directory paths
        for templates and static files.
    - GotifySettings:
        Configuration for Gotify notification service including server URL, app token,
        app name, and client token.
    - ClipboardWatcherSettings:
        Configuration for clipboard monitoring service including poll interval, thumbnail
        dimensions, and paste directory.
    - RedditSettings:
        PRAW client configuration for Reddit API access including client ID, secret, and
        user agent.
    - DatabaseSettings:
        PostgreSQL database connection configuration including user, password, host, port,
        and database name.
    - AuthSettings:
        Authentication configuration including JWT secret key, algorithm, token expiration,
        and admin credentials.
    - CliSettings:
        CLI-specific configuration including SQLite database path for caching with a
        convenience property for database access.
    - AppSettings:
        Global application settings including app root directory, environment, timezone,
        and computed properties for logs, cache, temp, and remotes directories.
Design Notes:
- All settings classes use Pydantic Field with aliases to support environment variable
    configuration (e.g., CONTROLLER_API_HOST, OLLAMA_MODEL).
- Default values are provided for all fields enabling zero-configuration startup in
    development environments.
- Path fields support both string and Path objects with automatic coercion.
- The timezone field in AppSettings includes a custom validator to parse integer hour
    offsets from environment variables.
- Sensitive fields (passwords, tokens, secrets) have placeholder defaults that should
    be overridden in production via environment variables.

"""

from sqlite_utils import Database

from lib.core.src.core.imports import (
    timedelta,
    timezone,
    Path,
    Any,
    Field,
    field_validator,
)
from core.config.base import APP_ROOT, TTS_MODELS_DIR
from core.config.factory import FactoryBaseSettings
from core.config.factory import get_settings  # noqa: F401  This is used externally


class ControllerAPISettings(FactoryBaseSettings):
    """
    Controller API configuration settings.
    """

    host: str = Field(
        default="localhost",
        alias="CONTROLLER_API_HOST",
        description="Host for the Controller API server.",
    )
    port: int = Field(
        default=8111,
        alias="CONTROLLER_API_PORT",
        description="Port for the Controller API server.",
    )
    log_level: str = Field(
        default="debug",
        alias="CONTROLLER_API_LOG_LEVEL",
        description="Log level for the Controller API server.",
    )


class OllamaSettings(FactoryBaseSettings):
    """
    Configuration for the Ollama LLM Service.
    """

    host: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_HOST",
        description="Host for the Ollama service.",
    )
    default_model: str = Field(
        default="gpt-oss:20b",
        alias="OLLAMA_MODEL",
        description="Default Ollama model to use.",
    )
    context_size: int = Field(
        default=65536,
        alias="OLLAMA_CTX",
        description="Context window size for the Ollama model.",
    )
    default_temperature: float = Field(
        default=0.7,
        alias="OLLAMA_TEMPERATURE",
        description="Default temperature setting for the Ollama model.",
    )
    default_top_k: int = Field(
        default=40,
        alias="OLLAMA_TOP_K",
        description="Default top_k setting for the Ollama model.",
    )
    default_top_p: float = Field(
        default=0.9,
        alias="OLLAMA_TOP_P",
        description="Default top_p setting for the Ollama model.",
    )
    embedding_model: str = Field(
        default="embeddinggemma",
        alias="OLLAMA_EMBEDDING_MODEL",
        description="Ollama model to use for embeddings.",
    )
    vl_model: str = Field(
        default="qwen",
        alias="OLLAMA_VL_MODEL",
        description="Ollama model to use for vision-language tasks.",
    )


class ConverterAPISettings(FactoryBaseSettings):
    """
    Converter API configuration settings.
    """

    host: str = Field(
        default="localhost",
        alias="CONVERTER_API_HOST",
        description="Host for the Converter API server.",
    )
    port: int = Field(
        default=8112,
        alias="CONVERTER_API_PORT",
        description="Port for the Converter API server.",
    )
    log_level: str = Field(
        default="debug",
        alias="CONVERTER_API_LOG_LEVEL",
        description="Log level for the Converter API server.",
    )


class MQTTSettings(FactoryBaseSettings):
    """
    Configuration for the MQTT Broker.
    """

    broker: str = Field(
        default="localhost",
        description="Host for the MQTT broker.",
        alias="MQTT_BROKER",
    )
    port: int = Field(
        default=1883,
        description="Port for the MQTT broker.",
        alias="MQTT_PORT",
    )
    username: str = Field(
        default="mqtt_user",
        description="Username for the MQTT broker.",
        alias="MQTT_USERNAME",
    )
    password: str = Field(
        default="mqtt_pass",
        description="Password for the MQTT broker.",
        alias="MQTT_PASSWORD",
    )
    topic_prefix: str = Field(
        default="controller-api",
        description="Topic prefix for the MQTT broker.",
        alias="MQTT_TOPIC_PREFIX",
    )


class TTSServerSettings(FactoryBaseSettings):
    """
    Configuration for the Piper TTS Service.
    """

    host: str = Field(
        default="localhost",
        description="Host for the TTS service.",
        alias="TTS_SERVER_HOST",
    )
    port: int = Field(
        default=8113,
        description="Port for the TTS service.",
        alias="TTS_SERVER_PORT",
    )
    log_level: str = Field(
        default="info",
        description="Log level for the TTS service.",
        alias="TTS_SERVER_LOG_LEVEL",
    )
    model_dir: Path = Field(
        default=TTS_MODELS_DIR or Path(APP_ROOT / "tts_models"),
        description="Directory where TTS models are stored.",
        alias="TTS_MODELS_DIR",
    )
    output_dir: Path = Field(
        default=APP_ROOT / "audio",
        description="Directory where generated audio files are stored.",
        alias="TTS_OUTPUT_DIR",
    )
    default_model: str = Field(
        default="en_US-libritts-high",
        description="Default TTS model to use.",
        alias="TTS_MODEL",
    )
    default_speaker: int = Field(
        default=0,
        description="Default speaker ID for multi-speaker models.",
        alias="TTS_SPEAKER_ID",
    )


class STTSettings(FactoryBaseSettings):
    """
    Configuration for the STT Service.
    """

    sample_rate: int = Field(
        default=16000,
        description="Sample rate for audio processing.",
        alias="STT_SAMPLE_RATE",
    )
    model_size: str = Field(
        default="large-v3",
        description="Size of the STT model to use.",
        alias="STT_MODEL",
    )
    log_level: str = Field(
        default="info",
        description="Log level for the STT service.",
        alias="STT_LOG_LEVEL",
    )
    port: int = Field(
        default=8114,
        description="Port for the STT service.",
        alias="STT_SERVICE_PORT",
    )
    host: str = Field(
        default="localhost",
        description="Host for the STT service.",
        alias="STT_SERVICE_HOST",
    )


class S3Settings(FactoryBaseSettings):
    """
    S3-compatible storage configuration settings.
    """

    # alias: str = os.getenv("S3_ALIAS", "minio")
    # """[str] Alias for the S3-compatible storage."""
    alias: str = Field(
        default="minio",
        description="Alias for the S3-compatible storage.",
        alias="S3_ALIAS",
    )
    endpoint_url: str = Field(
        default="http://localhost:9000",
        description="Endpoint URL for the S3-compatible storage.",
        alias="S3_ENDPOINT",
    )
    access_key: str = Field(
        default="minioadmin",
        description="Access key for the S3-compatible storage.",
        alias="S3_ACCESS_KEY",
    )
    secert_key: str = Field(
        default="minioadminpassword",
        description="Endpoint URL for the S3-compatible storage.",
        alias="S3_SECRET_KEY",
    )
    bucket_name: str = Field(
        default="utilsrvr-data",
        description="Name of the main S3 bucket for application data.",
        alias="S3_BUCKET",
    )
    s3_presigned_url_timeout: int = Field(
        default=3600,
        description="Expiration time for presigned URLs in seconds. DEFAULT: 3600 (1 hour)",
        alias="S3_PRESIGNED_URL_EXPIRATION",
    )

    # Buckets for specific types
    tts_bucket: str = "tts-audio"
    html_bucket: str = "html-content"
    docling_bucket: str = "docling-docs"
    cache_bucket: str = "cache-bucket"

    buckets: list[str] = [tts_bucket, docling_bucket, html_bucket, cache_bucket]
    """List of all required buckets."""


class UiServerSettings(FactoryBaseSettings):
    """
    Configuration for the UI Server.
    """

    host: str = Field(
        default="localhost",
        description="Host for the UI server.",
        alias="UI_SERVER_HOST",
    )
    port: int = Field(
        default=8115,
        description="Port for the UI server.",
        alias="UI_SERVER_PORT",
    )
    log_level: str = Field(
        default="debug",
        description="Log level for the UI server.",
        alias="UI_SERVER_LOG_LEVEL",
    )

    base_dir: Path = Field(
        default=Path(APP_ROOT / "src" / "ui_server"),
        description="Base directory for UI server templates.",
        frozen=True,
    )
    template_dir: Path = Field(
        default=Path(APP_ROOT / "src" / "ui_server" / "templates"),
        description="Directory for UI server HTML templates.",
        frozen=True,
    )
    static_dir: Path = Field(
        default=Path(APP_ROOT / "src" / "ui_server" / "static"),
        description="Directory for UI server static files.",
        frozen=True,
    )


class GotifySettings(FactoryBaseSettings):
    """
    Configuration for Gotify Notification Service.
    """

    server_url: str = Field(
        default="http://localhost:8080",
        description="Base URL for the Gotify server.",
        alias="GOTIFY_SERVER_URL",
    )
    app_token: str = Field(
        default="your_gotify_api_token",
        description="API token for authenticating with the Gotify server.",
        alias="GOTIFY_APPLICATON_API_TOKEN",
    )
    app_name: str = Field(
        default="ControllerAPI",
        description="Name of the service sending notifications.",
        alias="GOTIFY_APPLICATON_SERVICE_NAME",
    )
    client_token: str = Field(
        default="your_gotify_client_token",
        description="Client token for authenticating with the Gotify server.",
        alias="GOTIFY_CLIENT_TOKEN",
    )


class ClipboardWatcherSettings(FactoryBaseSettings):
    """
    Configuration for the Clipboard Watcher Service.
    """

    poll_interval: float = Field(
        default=1.0,
        description="Interval for polling the clipboard. (Seconds) [Default: 1.0]",
        alias="CLIPBOARD_WATCHER_POLL_INTERVAL",
    )
    thumbnail_dim: tuple[int, int] = Field(
        default=(512, 512),
        description="Size of the thumbnail to generate. (Width,Height) [Default: (512,512)]",
        alias="CLIPBOARD_WATCHER_THUMBNAIL_SIZE",
    )
    paste_directory: Path = Field(
        default=APP_ROOT / ".cache" / "clipboard",
        description="Directory for pasting clipboard content.",
        alias="CLIPBOARD_WATCHER_PASTE_DIRECTORY",
    )


class RedditSettings(FactoryBaseSettings):
    """
    PRAW Client configuration settings.
    """

    client_id: str = Field(
        default="your_client_id",
        description="Reddit API client ID.",
        alias="REDDIT_CLIENT_ID",
    )
    client_secret: str = Field(
        default="your_client_secret",
        description="Reddit API client secret.",
        alias="REDDIT_CLIENT_SECRET",
    )
    user_agent: str = Field(
        default="your_user_agent",
        description="User agent for Reddit API requests.",
        alias="REDDIT_USER_AGENT",
    )


class DatabaseSettings(FactoryBaseSettings):
    """
    Database configuration settings.
    """

    db_user: str = Field(
        default="postgres",
        alias="DB_USER",
        description="Postgres username.",
    )
    db_pass: str = Field(
        default="##postgres_admin_pass##",
        alias="DB_PASS",
        description="Postgres password.",
    )
    db_host: str = Field(
        default="localhost",
        alias="DB_HOST",
        description="Postgres host.",
    )
    db_port: str = Field(
        default="5432",
        alias="DB_PORT",
        description="Postgres port.",
    )
    db_name: str = Field(
        default="controller-api",
        alias="DB_NAME",
        description="Postgres database name.",
    )


class AuthSettings(FactoryBaseSettings):
    """
    Authentication configuration settings.
    """

    secret_key: str = Field(
        default="super-secret-key-change-me",
        alias="SECRET_KEY",
        description="Secret key for JWT and other security-related operations.",
    )
    algorithm: str = Field(
        default="HS256",
        alias="ALGORITHM",
        description="Algorithm used for JWT encoding and decoding.",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Access token expiration time in minutes.",
    )
    admin_username: str = Field(
        default="admin",
        alias="ADMIN_USERNAME",
        description="Admin username for the application.",
    )
    admin_password: str = Field(
        default="admin",
        alias="ADMIN_PASSWORD",
        description="Admin password for the application.",
    )


class CliSettings(FactoryBaseSettings):
    """
    CLI configuration settings.
    """

    cli_db_path: Path = Field(
        default=APP_ROOT / ".cache" / "cache.db",
        description="Path to the SQLite database file for CLI caching.",
        alias="CLI_DB_PATH",
    )

    @property
    def cli_db(self) -> Database:
        """SQLite database instance for CLI caching."""
        return Database(self.cli_db_path)


class AppSettings(FactoryBaseSettings):
    """Application configuration settings."""

    # Application Data Root
    app_root: Path = Field(
        default=Path(APP_ROOT),
        description="Root directory for application data storage.",
    )
    environment: str = Field(
        default="APP_ENV",
        description="Current application environment (prod, docker, dev).",
        alias="ENVIRONMENT",
    )
    tz: timezone = Field(
        default=timezone(timedelta(hours=0)),
        description="[timezone] Timezone for the server.",
        alias="SERVER_TIMEZONE_OFFSET_HOURS",
    )

    @property
    def logs_dir(self) -> Path:
        """Base directory for logs."""
        return self.app_root / "logs"

    @property
    def cache_dir(self) -> Path:
        """Base directory for cache."""
        return self.app_root / ".cache"

    @property
    def temp_dir(self) -> Path:
        """Base directory for temp files."""
        return self.app_root / ".temp"

    @property
    def remotes_dir(self) -> Path:
        """Base directory for remote files."""
        return self.app_root / "remotes"

    @field_validator("tz", mode="before")
    def parse_timezone(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                offset_hours = int(v)
                return timezone(timedelta(hours=offset_hours))
            except ValueError:
                pass
        return v
