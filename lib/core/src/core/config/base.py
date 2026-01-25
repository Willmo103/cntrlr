# region Docstring
"""
core.config.base

Environment detection and application configuration utilities.

Overview:
- Provides a utility class for detecting the current application environment
    (production, Docker, or development) based on environment variables or
    path-based heuristics.
- Exposes module-level constants for commonly needed configuration values
    such as application root directory, environment type, and TTS models directory.

Contents:
- Classes:
    - AppEnv:
        A utility class for environment detection and path resolution. Provides
        class methods to determine the current environment, retrieve the application
        root directory, and locate the TTS models directory based on the detected
        environment.

- Module-level Constants:
    - APP_ROOT (Path): The resolved root directory of the application.
    - APP_ENV (Literal["prod", "docker", "dev"]): The detected application environment.
    - TTS_MODELS_DIR (Path): The directory where TTS models are stored, resolved
        based on the current environment.

Environment Detection Logic:
- Priority 1: Checks the ENVIRONMENT environment variable for explicit configuration.
- Priority 2: Falls back to path-based detection:
    - Paths starting with "/app" indicate Docker environment.
    - Paths starting with "/srv" indicate production environment.
    - All other paths default to development environment.

Design Notes:
- Environment detection is performed at import time to ensure consistent behavior
    throughout the application lifecycle.
- Path resolution uses absolute paths to avoid ambiguity in different execution contexts.
- Development mode includes debug output to assist with configuration verification.

"""
# endregion
# region Imports
from lib.core.src.core.imports import os, Path, Literal

# endregion
# region AppEnv Class


class AppEnv:
    """
    Application environment detection utility.

    Attributes:
        ROOT (Path): The root directory of the application. Defaults to the current working directory.
        PROD (Literal["prod"]): Constant representing the production environment.
        DOCKER (Literal["docker"]): Constant representing the Docker environment.
        DEV (Literal["dev"]): Constant representing the development environment.
    """

    ROOT: Path = Path().cwd().resolve()
    PROD: Literal["prod"] = "prod"
    DOCKER: Literal["docker"] = "docker"
    DEV: Literal["dev"] = "dev"

    @classmethod
    def environment(cls) -> Literal["prod", "docker", "dev"]:
        """Determine the current application environment."""
        # Check ENVIRONMENT variable first; validate and return if set
        if os.getenv("ENVIRONMENT") in {cls.PROD, cls.DOCKER, cls.DEV}:
            return os.getenv("ENVIRONMENT")

        # Fallback to path-based detection
        calling_path = Path.cwd().as_posix()
        if calling_path.startswith("/app"):
            return cls.DOCKER
        elif calling_path.startswith("/srv"):
            return cls.PROD
        else:
            return cls.DEV

    @classmethod
    def app_root(cls) -> Path:
        """Get the application root directory."""
        return cls.ROOT

    @classmethod
    def tts_models_dir(cls) -> Path:
        """Get the TTS models directory based on the environment."""
        if cls.environment() == cls.DOCKER:
            return Path("/models").resolve()
        elif cls.environment() == cls.PROD:
            return Path("/srv/controller-api/tts_models").resolve()
        else:
            return Path(os.getenv("TTS_MODELS_DIR", cls.ROOT / "tts_models")).resolve()


# endregion
# region Module-level Constants

# Application Data Path
APP_ROOT: Path = AppEnv.app_root()
"""[Path] Root directory of the application."""
APP_ENV: Literal["prod", "docker", "dev"] = AppEnv.environment()
"""[Optional[Literal]] Environment type."""
TTS_MODELS_DIR: Path = AppEnv.tts_models_dir()
"""[Path] Directory where TTS models are stored."""
# endregion

if APP_ENV == "dev":
    print("Environment: {}".format(APP_ENV))
    print("TTS Models Dir: {}".format(TTS_MODELS_DIR.as_posix()))
    print("App Root: {}".format(APP_ROOT.as_posix()))
    input("Press Enter to continue...")


__all__ = [
    "APP_ENV",
    "APP_ROOT",
    "TTS_MODELS_DIR",
    "AppEnv",
]
