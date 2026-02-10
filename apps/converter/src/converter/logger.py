from datetime import datetime
import logging
from logging import Logger as T_Logger
from logging.config import dictConfig

from core.utils import get_time
from pythonjsonlogger.json import JsonFormatter  # type: ignore # noqa F401

from .config import INPUT_STORAGE_PATH, api_settings, app_root

__html_storage_path__ = INPUT_STORAGE_PATH / "html"
__document_storage_path__ = INPUT_STORAGE_PATH / "documents"
__log_file_path__ = app_root / "logs" / "converter_api.jsonl"
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
system_logger = logger.getChild("SYSTEM")
system_logger.debug("Logger for converter_api initialized.")


def _archive_daily_log_file():
    """Archive the log file daily by renaming it with a timestamp."""
    global __log_file_path__, system_logger
    system_logger.debug("Checking for log file to archive...")
    # look for an archaive from the last 24 hours
    current_time = get_time()
    # if an archive has a timestamp < 24 hours ago, skip archiving
    archive_files = sorted(__log_file_path__.parent.glob(f"{__log_file_path__.stem}_*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True) or []
    if archive_files:
        latest_archive = archive_files[0]
        timestamp_str = latest_archive.stem.replace(f"{__log_file_path__.stem}_", "")
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            system_logger.warning(f"Could not parse timestamp from archive file {latest_archive}, skipping timestamp check.")
            return
        if (current_time - timestamp).total_seconds() < 24 * 3600:
            system_logger.debug(f"Latest archive {latest_archive} is less than 24 hours old, skipping archiving.")
            return

    if __log_file_path__.exists():
        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        archive_path = __log_file_path__.with_name(f"{__log_file_path__.stem}_{timestamp}.jsonl")
        system_logger.debug(f"Archiving log file {__log_file_path__} to {archive_path}")
        __log_file_path__.rename(archive_path)


def _manage_logfile_archives(days_to_keep: int = 10):
    """Manage log file archives by keeping only the most recent ones."""
    global __log_file_path__, system_logger
    system_logger.debug("Managing log file archives...")
    archive_files = sorted(__log_file_path__.parent.glob(f"{__log_file_path__.stem}_*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True) or []
    if len(archive_files) <= days_to_keep:
        system_logger.debug("No old archive files to delete.")
        return
    for archive_file in archive_files[days_to_keep:]:
        system_logger.debug(f"Deleting old archive file: {archive_file}")
        archive_file.unlink()

# Archive the log file on startup
_archive_daily_log_file()
_manage_logfile_archives()
