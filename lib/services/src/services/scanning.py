# region Docstring
"""
Scanning Service Module
"""

# endregion
# region Imports
from datetime import datetime
from logging import Logger as T_Logger
from pathlib import Path
from typing import Any, Literal, Optional
from core.utils import get_time

import git
import sqlite_utils

from pydantic import Field, field_validator, model_serializer

from core.base import BaseModel
from core.config import AppSettings
from core.models import (  # noqa: F401
    ImageFile,
    ImageScanResult,
    ObsidianNote,
    ObsidianScanResult,
    Repo,
    RepoScanResult,
    VideoFile,
    VideoScanResult,
)


# endregion
# region Exceptions


class RepositoryCloningError(Exception):
    """Custom exception for repository cloning errors."""

    pass


class RepositoryNotFoundError(Exception):
    """Custom exception for repository not found errors."""

    pass


class RepositoryAlreadyExistsError(Exception):
    """Custom exception for repository already exists errors."""

    pass


# endregion
# revion Services


class LocalRepoIdxEntity(BaseModel):
    id: Optional[int] = Field(
        None, description="Primary key. (Assigned by DB `AUTOINCREMENT`)"
    )
    scan_path: Path = Field(
        ..., description="Path to the repository on the local filesystem"
    )
    storage_path: Optional[Path] = Field(
        None, description="Path where the repository is stored/cloned"
    )
    added_at: Optional[datetime] = Field(
        default=get_time(), description="Timestamp of the first scan"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the last scan"
    )

    @field_validator("scan_path", mode="before")
    def validate_path(cls, v: Any) -> Path:
        if isinstance(v, str):
            v = Path(v)
        if not isinstance(v, Path):
            raise ValueError("path must be a Path object")
        return v

    @field_validator("storage_path", mode="before")
    def validate_storage_path(cls, v: Any) -> Optional[Path]:
        if isinstance(v, str):
            v = Path(v)
        if v is not None and not isinstance(v, Path):
            raise ValueError("storage_path must be a Path object or None")
        return v

    @field_validator("added_at", "updated_at", mode="before")
    def validate_datetimes(cls, v: Any) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "id": self.id,
            "scan_path": str(self.scan_path),
            "storage_path": str(self.storage_path) if self.storage_path else None,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ClonedRepoIdxEntity(BaseModel):
    id: Optional[int] = Field(
        None, description="Primary key. (Assigned by DB `AUTOINCREMENT`)"
    )
    remote_url: str = Field(..., description="Remote URL of the repository")
    storage_path: Optional[Path] = Field(
        None, description="Local path where the repository is cloned"
    )
    added_at: Optional[datetime] = Field(
        default=get_time(), description="Timestamp of when the repo was cloned"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the last scan"
    )

    @field_validator("added_at", "updated_at", mode="before")
    def validate_datetimes(cls, v: Any) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class RepoManagementService:

    __logger: T_Logger
    __settings: AppSettings
    __db: sqlite_utils.Database
    __remotes_dir: Path

    def __init__(self, logger: T_Logger, settings: AppSettings) -> None:
        self.__logger = logger.getChild(self.__class__.__name__)
        self.__settings = settings
        self.__db = self.__settings.db
        self.__remotes_dir = self.__settings.remotes_dir
        if not self.__remotes_dir.exists():
            self.__logger.debug(f"Creating remotes directory at {self.__remotes_dir}")
            self.__remotes_dir.mkdir(parents=True, exist_ok=True)

    def __clone_repository(self, remote_url: str) -> Path:
        """Clone a repository from the given remote URL.

        Arguments:
            remote_url (str): The remote URL of the repository to clone.

        Returns:
            Path: The local path where the repository was cloned.

        Raises:
            RepositoryCloningError: If the cloning process fails.
        """
        try:
            repo_name = remote_url.split("/")[-1].replace(".git", "")
            local_path = self.__remotes_dir / repo_name
            if local_path.exists():
                raise RepositoryAlreadyExistsError(
                    f"Repository already exists at {local_path}"
                )
            self.__logger.info(f"Cloning repository from {remote_url} to {local_path}")
            git.Repo.clone_from(remote_url, local_path)
            entity = ClonedRepoIdxEntity(
                remote_url=remote_url,
                storage_path=local_path,
                added_at=get_time(),
            )
            self.__db["cloned_repos"].insert(entity.model_dump(exclude={"id"}, pk="id"))
            self.__logger.info(f"Successfully cloned repository to {local_path}")
            return local_path
        except Exception as e:
            self.__logger.error(f"Failed to clone repository: {e}")
            raise RepositoryCloningError(
                f"Failed to clone repository from {remote_url}"
            ) from e

    def __index_local_repository(self, scan_path: Path, copy: bool = False) -> Path:
        """
        Index a local repository by adding it to the database.

        Arguments:
            scan_path (Path): Path to the local repository.
            copy (bool): Whether to copy the repository to the managed remotes directory. Defaults to False.

        Returns:
            Path: The path where the repository is stored.

        Raises:
            RepositoryAlreadyExistsError: If the repository is already indexed.
        """

    def __get_indexed_repositories(
        self, repo_type: Literal["all", "cloned", "local"]
    ) -> list[ClonedRepoIdxEntity]:
        """Retrieve all indexed cloned repositories.

        Returns:
            list[ClonedRepoIdxEntity]: List of cloned repository entities.
        """
        ...

    def __get_git_files(self, repo_path: Path) -> list[str]:
        """Get a list of all tracked files in a Git repository.

        Arguments:
            repo_path (Path): Path to the local Git repository.

        Returns:
            list[str]: List of file paths tracked by Git.
        """

        try:
            repo = git.Repo(repo_path)
            git_files = repo.git.ls_files().splitlines()
            return git_files
        except Exception as e:
            self.__logger.error(f"Failed to get git files from {repo_path}: {e}")
            return []

    @property
    def remotes_dir(self) -> Path:
        """Return the root directory for cloning repositories."""
        return self.__settings.remotes_dir


# endregion
# region Exports
__all__ = []
