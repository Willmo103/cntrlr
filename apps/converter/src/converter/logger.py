import logging
from logging import Logger as T_Logger
from logging.config import dictConfig

from pythonjsonlogger.json import JsonFormatter  # type: ignore # noqa F401

from .config import INPUT_STORAGE_PATH, api_settings, app_root

__html_storage_path__ = INPUT_STORAGE_PATH / "html"
__document_storage_path__ = INPUT_STORAGE_PATH / "documents"
__log_file_path__ = app_root / "logs" / "converter_api.log"
__log_level__ = api_settings.log_level.upper()

# Ensure storage directories exist
__document_storage_path__.mkdir(parents=True, exist_ok=True)
__html_storage_path__.mkdir(parents=True, exist_ok=True)
__log_file_path__.parent.mkdir(parents=True, exist_ok=True)


config = {
    "version": 1,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(__log_file_path__),
            "formatter": "json",
            "level": __log_level__,
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": __log_level__,
        },
    },
    "loggers": {
        "converter_api": {
            "handlers": ["file", "console"],
            "level": __log_level__,
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": __log_level__,
    },
}
dictConfig(config)
logger: T_Logger = logging.getLogger("converter_api")
logger.debug("Logger for converter_api initialized.")
