"""
Application configuration module.
Defines application paths and environment detection.

Loads environment variables from a .env file if present.
"""

from core.imports import Literal, Path, os


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


# Application Data Path
APP_ROOT: Path = AppEnv.app_root()
"""[Path] Root directory of the application."""
APP_ENV: Literal["prod", "docker", "dev"] = AppEnv.environment()
"""[Optional[Literal]] Environment type."""
TTS_MODELS_DIR: Path = AppEnv.tts_models_dir()
"""[Path] Directory where TTS models are stored."""

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
