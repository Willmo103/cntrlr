# region Docstring
"""
Scanning Service Module
"""

# endregion
# region Imports
from datetime import datetime
from logging import Logger as T_Logger
import os
from pathlib import Path
from typing import Any, Generator, Literal, Optional, Union
from core.utils import get_time

import git
import sqlite_utils

from pydantic import Field, field_validator, model_serializer

from core.base import BaseModel
from core.config import AppSettings
from core.models import (  # noqa: F401
    GitCommit,
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
# region ServiceExceptions


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
# region ServiceTypes
class ScanRootEntity(BaseModel):
    """
    Entity representing a scan root in the database.

    Attributes:
        id (Optional[int]): Primary key. (Assigned by DB `AUTOINCREMENT`)
        path (Union[str]): Path to the scan root directory.
        details (Optional[str]): Additional details or description about the scan root.
        added_at (Optional[datetime]): Timestamp of when the scan root was added.
        updated_at (Optional[datetime]): Timestamp of the last update to the scan root.
    """

    id: Optional[int] = Field(
        None, description="Primary key. (Assigned by DB `AUTOINCREMENT`)"
    )
    path: Union[str] = Field(..., description="Path to the scan root directory")
    details: Optional[str] = Field(
        None, description="Additional details or description about the scan root"
    )
    added_at: Optional[datetime] = Field(
        default=get_time(), description="Timestamp of when the scan root was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the last update to the scan root"
    )

    @field_validator("added_at", "updated_at", mode="before")
    def validate_datetimes(cls, v: Any) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "details": self.details,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def Path(self) -> Path:
        return Path(self.path)


class LocalRepoIdxEntity(BaseModel):
    """
    Entity representing a locally indexed repository in the database.

    Attributes:
        id (Optional[int]): Primary key. (Assigned by DB `AUTOINCREMENT`)
        scan_path (Path): Path to the repository on the local filesystem.
        storage_path (Optional[Path]): Path where the repository is stored/cloned.
        added_at (Optional[datetime]): Timestamp of the first scan.
        updated_at (Optional[datetime]): Timestamp of the last scan.
    """

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
        """
        Serialize the model to a JSON-compatible dictionary.
        """
        return {
            "id": self.id,
            "scan_path": str(self.scan_path),
            "storage_path": str(self.storage_path) if self.storage_path else None,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ClonedRepoIdxEntity(BaseModel):
    """
    Entity representing a cloned repository in the database.

    Attributes:
        id (Optional[int]): Primary key. (Assigned by DB `AUTOINCREMENT`)
        remote_url (str): Remote URL of the repository.
        storage_path (Optional[Path]): Local path where the repository is cloned.
        added_at (Optional[datetime]): Timestamp of when the repo was cloned.
        updated_at (Optional[datetime]): Timestamp of the last scan.
    """

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


# endregion
# region Services


class RepoIndex:
    """
    Service for managing indexed repositories.

    Attributes:
        __logger (Logger): The logger instance.
        __settings (AppSettings): The application settings.
        __db (sqlite_utils.Database): The database instance.
        __remotes_dir (Path): The directory where remote repositories are cloned.
    """

    __logger: T_Logger
    __settings: AppSettings
    __db: sqlite_utils.Database
    __remotes_dir: Path

    def __init__(self, logger: T_Logger, settings: AppSettings) -> None:
        """
        Initialize the RepoIndex service.

        Arguments:
            logger (Logger): The logger instance.
            settings (AppSettings): The application settings.
        """
        self.__logger = logger.getChild(self.__class__.__name__)
        self.__settings = settings
        self.__db = self.__settings.db
        self.__remotes_dir = self.__settings.remotes_dir
        if not self.__remotes_dir.exists():
            self.__logger.debug(f"Creating remotes directory at {self.__remotes_dir}")
            self.__remotes_dir.mkdir(parents=True, exist_ok=True)

    def __get_cloned_repositories(self) -> list[ClonedRepoIdxEntity]:
        """
        Retrieve all cloned repositories from the database.

        Returns:
            list[ClonedRepoIdxEntity]: List of cloned repositories.
        """
        rows = self.__db["cloned_repos"].rows
        repos = []
        for row in rows:
            entity = ClonedRepoIdxEntity(
                id=row["id"],
                remote_url=row["remote_url"],
                storage_path=Path(row["storage_path"]) if row["storage_path"] else None,
                added_at=row["added_at"],
                updated_at=row["updated_at"],
            )
            repos.append(entity)
        return repos

    def __get_local_repositories(self) -> list[LocalRepoIdxEntity]:
        """
        Retrieve all indexed local repositories from the database.

        Returns:
            list[LocalRepoIdxEntity]: List of indexed local repositories.
        """
        rows = self.__db["local_repos"].rows
        repos = []
        for row in rows:
            entity = LocalRepoIdxEntity(
                id=row["id"],
                scan_path=Path(row["scan_path"]),
                storage_path=Path(row["storage_path"]) if row["storage_path"] else None,
                added_at=row["added_at"],
                updated_at=row["updated_at"],
            )
            repos.append(entity)
        return repos

    def __add_remote_repository(self, remote_url: str) -> Path:
        """Clone a repository from the given remote URL into the REMOTES_DIR.

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

    def __add_local_repository(self, scan_path: Path, copy: bool = False) -> Path:
        """
        Add a local repository to the index.

        Arguments:
            scan_path (Path): Path to the local repository.
            copy (bool): Whether to copy the repository to the managed remotes directory. Defaults to False.

        Returns:
            Path: The path where the repository is stored.
        """
        storage_path = self.__remotes_dir / scan_path.name if copy else scan_path
        try:
            existing = self.__db["local_repos"].rows_where(
                "scan_path = ?", [str(scan_path)]
            )
            if existing:
                raise RepositoryAlreadyExistsError(
                    f"Repository at {scan_path} is already indexed."
                )
            if copy:
                import shutil

                storage_path = self.__remotes_dir / scan_path.name
                self.__logger.info(
                    f"Copying repository from {scan_path} to {storage_path}"
                )
                shutil.copytree(scan_path, storage_path)
            entity = LocalRepoIdxEntity(
                scan_path=scan_path,
                storage_path=storage_path if copy else None,
                added_at=get_time(),
            )
            self.__db["local_repos"].insert(entity.model_dump(exclude={"id"}, pk="id"))
            self.__logger.info(f"Successfully added repository at {scan_path}")
            return scan_path
        except Exception as e:
            self.__logger.error(f"Failed to add local repository: {e}")
            raise

    def __iter_remotes_dir(self) -> list[Path]:
        """
        Iterate over the repositories in the remotes directory.

        Returns:
            list[Path]: List of repository paths.
        """
        repos = []
        for item in self.__remotes_dir.iterdir():
            if item.is_dir():
                repos.append(item)
        return repos

    def repos(self, type: Literal["cloned", "local", "all"]) -> list[BaseModel]:
        """
        Get a list of repositories based on their type.

        Arguments:
            type (Literal["cloned", "local"]): Type of the repositories to retrieve.

        Returns:
            list[BaseModel]: List of repositories.
        """
        if type == "cloned":
            return self.__get_cloned_repositories()
        elif type == "local":
            return self.__get_local_repositories()
        elif type == "all":
            return self.__get_cloned_repositories() + self.__get_local_repositories()
        else:
            raise ValueError("Invalid repository type specified.")

    def add_local_repo(self, scan_path: Path, copy: bool = False) -> Path:
        """
        Public method to add a local repository.

        Arguments:
            scan_path (Path): Path to the local repository.
            copy (bool): Whether to copy the repository to the managed remotes directory. Defaults to False.

        Returns:
            Path: The path where the repository is stored.
        """
        return self.__add_local_repository(scan_path, copy)

    def add_remote_repo(self, remote_url: str) -> Path:
        """
        Public method to add a remote repository.

        Arguments:
            remote_url (str): The remote URL of the repository to clone.

        Returns:
            Path: The local path where the repository was cloned.
        """
        return self.__add_remote_repository(remote_url)

    def update_all_remotes(
        self,
    ) -> Generator[tuple[Path, bool, Optional[str]], None, None]:
        """
        Pulls changes for all repos cloned-into or copied the REMOTES_DIR; yielding results for each operation.

        Yields:
            Generator[tuple[Path, bool, Optional[str]], None, None]: A generator yielding tuples of
            (repo_path, success_flag, error_message).

        Raises:
            RepositoryNotFoundError: If a repository is not found in the remotes directory.
        """
        for repo_path in self.__iter_remotes_dir():
            try:
                repo = git.Repo(repo_path)
                origin = repo.remotes.origin
                self.__logger.info(f"Pulling updates for repository at {repo_path}")
                origin.pull()
                yield (repo_path, True, None)
            except Exception as e:
                self.__logger.error(f"Failed to update repository at {repo_path}: {e}")
                yield (repo_path, False, str(e))

    def update_all_locals(
        self,
        in_place: bool = True,
    ) -> Generator[tuple[Path, bool, Optional[str]], None, None]:
        """
        Scans all indexed local repositories for changes; yielding results for each operation.

        Yields:
            Generator[tuple[Path, bool, Optional[str]], None, None]: A generator yielding tuples of
            (repo_path, success_flag, error_message).

        Raises:
            RepositoryNotFoundError: If a repository is not found in the index.
        """
        local_repos = self.__get_local_repositories()
        for repo_entity in local_repos:
            repo_path = repo_entity.scan_path if in_place else repo_entity.storage_path
            if not repo_path.exists():
                error_msg = f"Repository at {repo_path} not found."
                self.__logger.error(error_msg)
                yield (repo_path, False, error_msg)
                continue
            try:
                self.__logger.info(
                    f"Scanning local repository at {repo_path} for changes"
                )
                repo = git.Repo(repo_path)
                repo.git.fetch()
                yield (repo_path, True, None)
            except Exception as e:
                self.__logger.error(f"Failed to scan repository at {repo_path}: {e}")
                yield (repo_path, False, str(e))


class LocalRepoScanner:
    """
    Service for scanning directories to locate Git repositories.

    Attributes:
        __logger (Logger): The logger instance.
        __settings (AppSettings): The application settings.
        __db (sqlite_utils.Database): The database instance.
        __index (RepoIndex): The repository index instance.
    """

    __logger: T_Logger
    __settings: AppSettings
    __db: sqlite_utils.Database
    __index: RepoIndex

    def __init__(self, logger: T_Logger, settings: AppSettings) -> None:
        """
        Initialize the RepoScanner service.

        Arguments:
            logger (Logger): The logger instance.
            settings (AppSettings): The application settings.
        """
        self.__logger = logger.getChild(self.__class__.__name__)
        self.__settings = settings
        self.__db = self.__settings.db
        self.__index = RepoIndex(logger, settings)

    def __locate_repos(
        self, base_path: Path, recursive: bool = True
    ) -> Generator[Path, None, None]:
        """
        Locate Git repositories within the specified base path.

        Arguments:
            base_path (Path): The base directory to search for repositories.
            recursive (bool): Whether to search recursively. Defaults to True.

        Yields:
            Generator[Path, None, None]: A generator yielding paths to located repositories.
        """
        self.__logger = self.__logger.debug("Locating repositories...")
        if recursive:
            for dirpath, dirnames, filenames in os.walk(base_path):
                if ".git" in dirnames:
                    yield Path(dirpath)
                    dirnames.remove(".git")  # Prevent descending into .git directories
        else:
            for item in base_path.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    yield item

    def __index_repos(
        self,
        base_path: Path,
        recursive: bool = True,
        copy: bool = False,
    ) -> Generator[Path, None, None]:
        """
        Locate and index Git repositories within the specified base path.

        Arguments:
            base_path (Path): The base directory to search for repositories.
            recursive (bool): Whether to search recursively. Defaults to True.
            copy (bool): Whether to copy local repositories to the managed remotes directory. Defaults to False.

        Yields:
            Generator[Path, None, None]: A generator yielding paths to indexed repositories.
        """
        for repo_path in self.__locate_repos(base_path, recursive):
            try:
                self.__index.add_local_repo(repo_path, copy)
                yield repo_path
            except RepositoryAlreadyExistsError:
                self.__logger.info(f"Repository at {repo_path} is already indexed.")
            except Exception as e:
                self.__logger.error(f"Failed to index repository at {repo_path}: {e}")

    def scan(
        self,
        base_path: Path,
        recursive: bool = True,
        copy: bool = False,
    ) -> Generator[Path, None, None]:
        """
        Public method to scan and index Git repositories.

        Arguments:
            base_path (Path): The base directory to search for repositories.
            recursive (bool): Whether to search recursively. Defaults to True.
            copy (bool): Whether to copy local repositories to the managed remotes directory. Defaults to False.
        Yields:
            Generator[Path, None, None]: A generator yielding paths to indexed repositories.
        """
        return self.__index_repos(base_path, recursive, copy)


class ScanRootManager:
    """
    Manage scan roots in the database.

    Attributes:
        __db (sqlite_utils.Database): The database instance.
        __logger (T_Logger): The logger instance.
        __settings (AppSettings): The application settings.
        SCAN_ROOTS_TABLE (str): The name of the scan roots table in the database.
    """

    __db: sqlite_utils.Database
    __logger: T_Logger
    __settings: AppSettings
    SCAN_ROOTS_TABLE: str = "scan_roots"

    def __init__(self, logger: T_Logger, settings: AppSettings) -> None:
        """
        Initialize the ScanRootManager service.

        Arguments:
            logger (Logger): The logger instance.
            settings (AppSettings): The application settings.
        """
        self.__logger = logger.getChild(self.__class__.__name__)
        self.__settings = settings
        self.__db = self.__settings.db

    def _check_existing(self, path: Path) -> bool:
        """
        Check if a scan root already exists in the database.

        Arguments:
            path (Path): The path to check.

        Returns:
            bool: True if the scan root exists, False otherwise.
        """
        existing = self.__db[self.SCAN_ROOTS_TABLE].rows_where("path = ?", [str(path)])
        return len(existing) > 0

    def add_scan_root(
        self, path: Path, details: Optional[str] = None
    ) -> ScanRootEntity:
        """
        Add a new scan root to the database.

        Arguments:
            path (Path): The path of the scan root.
            details (Optional[str]): Additional details about the scan root.

        Returns:
            ScanRootEntity: The added scan root entity.

        Raises:
            ValueError: If the scan root already exists.
        """
        if self._check_existing(path):
            raise ValueError(f"Scan root at {path} already exists.")
        entity = ScanRootEntity(
            path=str(path),
            details=details,
            added_at=get_time(),
        )
        self.__db[self.SCAN_ROOTS_TABLE].insert(
            entity.model_dump(exclude={"id"}, pk="id")
        )
        self.__logger.info(f"Successfully added scan root at {path}")
        return entity

    def list_scan_roots(self) -> list[ScanRootEntity]:
        """
        List all scan roots in the database.

        Returns:
            list[ScanRootEntity]: List of scan root entities.
        """
        rows = self.__db[self.SCAN_ROOTS_TABLE].rows
        scan_roots = []
        for row in rows:
            entity = ScanRootEntity(
                id=row["id"],
                path=row["path"],
                details=row["details"],
                added_at=row["added_at"],
                updated_at=row["updated_at"],
            )
            scan_roots.append(entity)
        return scan_roots

    def remove_scan_root(self, path: Path) -> None:
        """
        Remove a scan root from the database.

        Arguments:
            path (Path): The path of the scan root to remove.

        Raises:
            ValueError: If the scan root does not exist.
        """
        existing = self._check_existing(path)
        if not existing:
            raise ValueError(f"Scan root at {path} does not exist.")
        self.__db[self.SCAN_ROOTS_TABLE].delete_where("path = ?", [str(path)])
        self.__logger.info(f"Successfully removed scan root at {path}")

    def update_scan_root(self, path: Path, new_details: Optional[str] = None) -> None:
        """
        Update the details of an existing scan root.

        Arguments:
            path (Path): The path of the scan root to update.
            new_details (Optional[str]): The new details to set.

        Raises:
            ValueError: If the scan root does not exist.
        """
        existing = self._check_existing(path)
        if not existing:
            raise ValueError(f"Scan root at {path} does not exist.")
        update_data = {"updated_at": get_time()}
        if new_details is not None:
            update_data["details"] = new_details
        self.__db[self.SCAN_ROOTS_TABLE].update_where(
            "path = ?", update_data, [str(path)]
        )
        self.__logger.info(f"Successfully updated scan root at {path}")


# endregion


__all__ = []
