# region Docstring
"""
Scanning Service Module
"""
# endregion
# region Imports
from datetime import datetime
from pathlib import Path
from core.models import (  # noqa: F401
    Repo,
    RepoScanResult,
    ObsidianNote,
    ObsidianScanResult,
    ImageFile,
    ImageScanResult,
    VideoFile,
    VideoScanResult,
)
from logging import Logger as T_Logger
from core.config import AppSettings
from core.models.file_system.base import BaseModel
from pydantic import Field


# endregion
# revion Services
class RepoScannerCacheEntry(BaseModel):
    repo_type: str = Field(
        ..., description="Type of the repository (e.g., 'git', 'obsidian')"
    )
    path: Path = Field(
        ..., description="Path to the repository on the local filesystem"
    )
    last_scanned_at: datetime = Field(..., description="Timestamp of the last scan")


class RepoScanningService:
    __logger: T_Logger
    __settings: AppSettings
    __cache_file: Path

    def __init__(self, logger: T_Logger, settings: AppSettings) -> None:
        self.__logger = logger.getChild(self.__class__.__name__)
        self.__settings = settings
        # computed properties

    def _get_timestamp(self) -> datetime:
        """Return the current UTC timestamp."""
        return datetime.now(tz=self.__settings.tz)

    @property
    def clone_root(self) -> Path:
        """Return the root directory for cloning repositories."""
        return self.__settings.remotes_dir


# endregion
# region Exports
__all__ = []
