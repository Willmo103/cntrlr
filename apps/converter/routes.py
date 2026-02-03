from logging import logger, FileHandler, StreamHandler, Formatter, Logger
from config import INPUT_STORAGE_PATH, app_settings, api_settings
from pythonjsonlogger import jsonlogger

__html_storage_path__ = INPUT_STORAGE_PATH / "html"
__document_storage_path__ = INPUT_STORAGE_PATH / "documents"
__log_file_path__ = app_settings.app_root / "logs" / "converter_api.log"
__log_level__ = api_settings.log_level
__document_storage_path__.mkdir(parents=True, exist_ok=True)
__html_storage_path__.mkdir(parents=True, exist_ok=True)
__log_file_path__.parent.mkdir(parents=True, exist_ok=True)
