# region Docstring
"""
Core utility functions for the cntrlr library.
This module provides a collection of utility functions organized into three main categories:
General Utilities
-----------------
Functions for common tasks like file type detection and format conversion:
- is_markdown_formattable: Check if a path has a markdown file extension
- is_image_file: Check if a path is an image file based on extension
- is_video_file: Check if a path is a video file based on extension
- get_markdown_format: Get the markdown format for a given file suffix
- is_data_file: Check if a path is a data file based on extension
- get_sqlite_schema: Retrieve SQLite database schema as a string
- get_sqlite_tables: Retrieve list of table names from a SQLite database
File Utilities
--------------
Functions for file operations and model creation:
- get_file_sha256: Calculate the SHA256 hash of a file
- get_file_stat_model: Get OS-appropriate file stat model
- get_path_model: Get the PathModel for a given file path
- get_mime_type: Get the MIME type of a file based on extension
- BaseFileModel_from_Path: Create a BaseFileModel from a file path
- ImageFileModel_from_Path: Create an ImageFileModel from an image file path
- VideoFileModel_from_Path: Create a VideoFileModel from a video file path
- SqliteFileModel_from_Path: Create a SQLiteFileModel from a database file path
- AudioFileModel_from_Path: Create an AudioFileModel from an audio file path (not yet implemented)
Git Utilities
-------------
Functions for git repository operations:
- get_git_metadata: Extract comprehensive git metadata from a repository
- get_latest_commit: Get the latest commit information
- get_all_commits: Get a list of commits from the repository
- get_repo_name: Get the repository name
- clone_repository: Clone a git repository to a specified path
Dependencies
------------
- pathlib.Path: For file path operations
- git: For git repository operations
- core.constants: For file format lists and extensions
- core.base: For file stat and path models
- core.models: For file and git metadata models
"""

# endregion
# region Imports
# import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Union

import git

from core.constants import (
    DATA_FORMAT_LIST,
    IMAGE_FORMAT_LIST,
    MARKDOWN_EXTENSIONS,
    MD_XREF,
    TZ_OFFSET,
    VIDEO_FORMAT_LIST,
)

# endregion
# region General Utilities
# General utility functions for various tasks.


def is_markdown_formattable(path: Path) -> bool:
    """Check if the given path has a markdown file extension.

    Args:
        path (Path): The file path to check.

    Returns:
        bool: True if the file is a markdown file, False otherwise.

    Example:
        >>> is_markdown_formattable(Path("document.md"))
        True
        >>> is_markdown_formattable(Path("image.png"))
        False
    """
    return path.suffix.lower() in MARKDOWN_EXTENSIONS


def is_image_file(path: Path) -> bool:
    """
    Check if the given path is an image file based on its extension.

    Args:
        path (Path): The file path to check.

    Returns:
        bool: True if the file is an image file, False otherwise.

    Example:
        >>> is_image_file(Path("photo.jpg"))
        True
        >>> is_image_file(Path("video.mp4"))
        False
    """
    return path.suffix.lower() in IMAGE_FORMAT_LIST


def is_video_file(path: Path) -> bool:
    """
    Check if the given path is a video file based on its extension.

    Args:
        path (Path): The file path to check.

    Returns:
        bool: True if the file is a video file, False otherwise.

    Example:
        >>> is_video_file(Path("movie.mp4"))
        True
        >>> is_video_file(Path("document.pdf"))
        False
    """
    return path.suffix.lower() in VIDEO_FORMAT_LIST


def get_markdown_format(suffix: str) -> str | None:
    """
    Get the markdown format corresponding to the given file suffix.

    Args:
        suffix (str): The file suffix (including the dot).

    Returns:
        str | None: The markdown format if found, otherwise 'plaintext'.

    Example:
        >>> get_markdown_format('.md')
        'markdown'
        >>> get_markdown_format('.txt')
        'plaintext'
    """
    return MD_XREF.get(suffix.lower(), "plaintext")


def is_data_file(path: Path) -> bool:
    """
    Check if the given path is a data file based on its extension.

    Args:
        path (Path): The file path to check.

    Returns:
        bool: True if the file is a data file, False otherwise.

    Example:
        >>> is_data_file(Path("data.csv"))
        True
        >>> is_data_file(Path("image.png"))
        False
    """
    return path.suffix.lower() in DATA_FORMAT_LIST


def get_sqlite_schema(path: Path) -> str:
    """
    Retrieve the SQLite database schema as a string.

    Args:
        path (Path): The file path to the SQLite database.

    Returns:
        str: The SQLite database schema.

    Raises:
        ValueError: If the provided path is not a valid SQLite database file.

    Example:
        >>> get_sqlite_schema(Path("database.db"))
        'CREATE TABLE ...'
    """
    import subprocess
    import sys

    try:
        cmd = ["sqlite-utils", "schema", path.as_posix()]

        if sys.platform == "win32":
            # On Windows, use 'python -m' to invoke the module
            cmd = [sys.executable, "-m", "sqlite_utils", "schema", path.as_posix()]
        else:
            cmd = ["sqlite-utils", "schema", path.as_posix()]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise ValueError(f"Error retrieving schema: {result.stderr.strip()}")
        return result.stdout
    except Exception as e:
        raise ValueError(f"Error retrieving schema: {str(e)}") from e


def get_sqlite_tables(path: Path) -> list[str]:
    """
    Retrieve the list of table names from a SQLite database.

    Args:
        path (Path): The file path to the SQLite database.

    Returns:
        list[str]: A list of table names in the database.

    Raises:
        ValueError: If the provided path is not a valid SQLite database file.

    Example:
        >>> get_sqlite_tables(Path("database.db"))
        ['users', 'orders', 'products']
        >>> get_sqlite_tables(Path("nonexistent.db"))
        []
    """
    import sqlite_utils

    try:
        _ = sqlite_utils.Database(path.as_posix())
        return _.table_names()
    except sqlite_utils.db.InvalidDatabase:
        raise ValueError(f"Invalid SQLite database file: {path}")
    except Exception as e:
        raise ValueError(f"Error retrieving tables: {str(e)}") from e


# endregion
# region File Utilities
# Utility functions for file operations.

# Functions:
# - get_file_sha256: Calculate the SHA256 hash of a file.
# - get_file_stat_model: Get the appropriate file stat model based on the OS.
# - get_path_model: Get the PathModel for a given file path.
# - get_mime_type: Get the MIME type of a file based on its extension.
# - extract_audio_track_from_video: Extract the audio track from a video file.
# - BaseFileModel_from_Path: Create a BaseFileModel instance from a given file path.
# - ImageFileModel_from_Path: Create an ImageFileModel instance from a given file path.
# - VideoFileModel_from_Path: Create a VideoFileModel instance from a given file path.
# - SqliteFileModel_from_Path: Create a SQLiteFileModel instance from a given file path.
# - AudioFileModel_from_Path: Create an AudioFileModel instance from a given file path. (Not yet implemented)


def get_file_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 hash of a file.

    Arguments:
        file_path (Path): The file path to calculate the hash for.

    Returns:
        str: The SHA256 hash as a hexadecimal string.

    Raises:
        RuntimeError: If there is an error reading the file.

    Example:
        >>> sha256 = get_file_sha256(Path("document.txt"))
        >>> print(sha256)
        '3a7bd3e2360a3d80c4f1b...'
    """
    import hashlib

    sha256_hash = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Error calculating SHA256 for file {file_path}: {e}") from e


def get_file_stat_model(file_path: Path) -> Union["BaseFileStat", "LinuxFileStat", "MacOSFileStat", "WindowsFileStat"]:  # type: ignore  # noqa: F821
    """
    Get the appropriate file stat model based on the operating system.

    Arguments:
        file_path (Path): The file path to get stats for.

    Returns:
        BaseFileStatModel: The corresponding file stat model instance.

    Example:
        >>> stat_model = get_file_stat_model(Path("/home/user/document.txt"))
        >>> print(stat_model)
        LinuxFileStatModel(...)
    """
    from core.base import (
        BaseFileStat,
    )  # , LinuxFileStat, MacOSFileStat, WindowsFileStat,
    from os import stat as os_stat

    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        file_stat = os_stat(file_path)

        # system = sys.platform
        # if system == "Darwin":
        #     return MacOSFileStat.model_validate(
        #         {
        #             stat_key: getattr(file_stat, stat_key)
        #             for stat_key in dir(file_stat)
        #             if not stat_key.startswith("_")
        #         }, from_attributes=True
        #     )
        # elif system == "Windows":
        #     return WindowsFileStat.model_validate(
        #         {
        #             stat_key: getattr(file_stat, stat_key)
        #             for stat_key in dir(file_stat)
        #             if not stat_key.startswith("_")
        #         }, from_attributes=True
        #     )
        # elif system == "Linux":
        #     return LinuxFileStat.model_validate(
        #         {
        #             stat_key: getattr(file_stat, stat_key)
        #             for stat_key in dir(file_stat)
        #             if not stat_key.startswith("_")
        #         }, from_attributes=True
        #     )
        # else:
        return BaseFileStat.model_validate(
            {
                stat_key: getattr(file_stat, stat_key)
                for stat_key in dir(file_stat)
                if not stat_key.startswith("_")
            },
            from_attributes=True,
        )
    except Exception as e:
        raise RuntimeError(f"Error getting file stat for {file_path}: {e}") from e


def get_path_model(file_path: Path) -> "PathModel":  # type: ignore  # noqa: F821
    """
    Get the PathModel for a given file path.

    Arguments:
        file_path (Path): The file path to model.
    Returns:
        PathModel: The corresponding PathModel instance.

    Example:
        >>> path_model = get_path_model(Path("/home/user/document.txt"))
        >>> print(path_model)
        PathModel(...)
    """
    from core.base import FilePath

    return FilePath(
        name=file_path.name,
        suffix=file_path.suffix,
        suffixes=file_path.suffixes,
        stem=file_path.stem,
        parent=str(file_path.parent),
        parents=[str(p) for p in file_path.parents],
        anchor=file_path.anchor,
        drive=file_path.drive,
        root=file_path.root,
        parts=[p for p in file_path.parts],
        is_absolute=file_path.is_absolute(),
    )


def get_mime_type(file_path: Path) -> str:
    """
    Get the MIME type of a file based on its extension.

    Arguments:
        file_path (Path): The file path to get the MIME type for.

    Returns:
        str | None: The MIME type if found, otherwise None.

    Example:
        >>> get_mime_type(Path("document.txt"))
        'text/plain'
        >>> get_mime_type(Path("image.jpg"))
        'image/jpeg'
    """
    try:
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_path.as_posix(), strict=False)
        if mime_type is None:
            return "application/octet-stream"
    except Exception as e:
        raise RuntimeError(f"Error getting MIME type for file {file_path}") from e


def BaseFileModel_from_Path(file_path: Path) -> "BaseFileModel":  # type: ignore  # noqa: F821
    """
    Create a BaseFileModel instance from a given file path.

    Args:
        file_path (Path): The path to the file.

    Returns:
        BaseFileModel: An instance of BaseFileModel populated with data from the file.

    Raises:
        RuntimeError: If there is an error creating the BaseFileModel.

    Example:
        >>> file_model = BaseFileModel_from_Path(Path("document.txt"))
        >>> print(file_model)
        BaseFileModel(...)
    """
    from core.base import BaseFileModel

    try:
        return BaseFileModel.populate(file_path)
    except Exception as e:
        raise RuntimeError(
            f"Error creating BaseFileModel from path {file_path}: {e}"
        ) from e


def ImageFileModel_from_Path(file_path: Path) -> "ImageFile":  # type: ignore  # noqa: F821
    """
    Create an ImageFileModel instance from a given file path.

    Args:
        file_path (Path): The path to the image file.

    Returns:
        Optional[ImageFileModel]: An instance of ImageFileModel populated with data from the file.

    Raises:
        RuntimeError: If there is an error creating the ImageFileModel.

    Example:
        >>> img_model = ImageFileModel_from_Path(Path("photo.jpg"))
        >>> print(img_model)
        ImageFileModel(...)
    """
    from core.models.file_system.image_file import ImageFile

    try:
        return ImageFile.populate(file_path)
    except Exception as e:
        raise RuntimeError(
            f"Error creating ImageFileModel from path {file_path}: {e}"
        ) from e


def VideoFileModel_from_Path(file_path: Path) -> "VideoFile":  # type: ignore  # noqa: F821
    """
    Create a VideoFileModel instance from a given file path.

    Args:
        file_path (Path): The path to the video file.

    Returns:
        VideoFileModel: An instance of VideoFileModel populated with data from the file.

    Raises:
        RuntimeError: If there is an error creating the VideoFileModel.

    Example:
        >>> video_model = VideoFileModel_from_Path(Path("movie.mp4"))
        >>> print(video_model)
        VideoFileModel(...)
    """
    from core.models.file_system.video_file import VideoFile

    try:
        return VideoFile.populate(file_path)
    except Exception as e:
        raise RuntimeError(
            f"Error creating VideoFileModel from path {file_path}: {e}"
        ) from e


def SqliteFileModel_from_Path(file_path: Path) -> "SQLiteFile":  # type: ignore  # noqa: F821
    """
    Create a SQLiteFileModel instance from a given file path.

    Args:
        file_path (Path): The path to the SQLite database file.

    Returns:
        SQLiteFileModel: An instance of SQLiteFileModel populated with data from the file.

    Raises:
        RuntimeError: If there is an error creating the SQLiteFileModel.

    Example:
        >>> sqlite_model = SqliteFileModel_from_Path(Path("database.sqlite"))
        >>> print(sqlite_model)
        SQLiteFileModel(...)
    """
    from core.models.file_system import SQLiteFile

    try:
        return SQLiteFile.populate(file_path)
    except Exception as e:
        raise RuntimeError(
            f"Error creating SQLiteFileModel from path {file_path}: {e}"
        ) from e


def AudioFileModel_from_Path(file_path: Path) -> "AudioFile":  # type: ignore  # noqa: F821
    """
    Create an AudioFileModel instance from a given file path.

    Args:
        file_path (Path): The path to the audio file.

    Raises:
        NotImplementedError: This function is not yet implemented.

    Example:
        >>> audio_model = AudioFileModel_from_Path(Path("song.mp3"))
        >>> print(audio_model)
        AudioFileModel(...)
    """
    from core.models.file_system.audio_file import AudioFile

    try:
        return AudioFile.populate(file_path)
    except Exception as e:
        raise RuntimeError(
            f"Error creating AudioFileModel from path {file_path}: {e}"
        ) from e


# endregion
# region Git Utilities
# Utility functions for git repository operations.


def get_git_metadata(repo_path: Path) -> Optional["GitMetadata"]:  # type: ignore  # noqa: F821
    """
    Extract git metadata from repository.

    Arguments:
        repo_path (Path): The path to the git repository.

    Returns:
        Optional[GitMetadata]: The git metadata if the path is a valid git repository, otherwise
        None.

    Example:
        >>> metadata = get_git_metadata(Path("/path/to/repo"))
        >>> print(metadata)
        GitMetadata(...)
    """
    from core.models.repo import GitCommit, GitMetadata

    if not (repo_path / ".git").exists() or not repo_path.is_dir():
        return None
    try:
        repo = git.Repo(repo_path)

        # Get remotes
        remotes = {remote.name: remote.url for remote in repo.remotes}

        # Get current branch
        try:
            current_branch = repo.active_branch.name
        except TypeError:
            current_branch = "HEAD (detached)"

        # Get all branches
        branches = [branch.name for branch in repo.branches]

        # Get commit info
        try:
            latest_commit = repo.head.commit
            commit_info = GitCommit(
                hash=latest_commit.hexsha[:8],
                message=latest_commit.message.strip(),
                author=str(latest_commit.author),
                date=latest_commit.committed_datetime.isoformat(),
            )
        except Exception:
            commit_info = {"error": "Unable to get commit info"}

        # Check for uncommitted changes
        is_dirty = repo.is_dirty()
        untracked_files = len(repo.untracked_files)

        return GitMetadata(
            remotes=remotes,
            current_branch=current_branch,
            branches=branches,
            latest_commit=commit_info,
            uncommitted_changes=is_dirty,
            untracked_files=untracked_files,
            commit_history=get_all_commits(repo_path, max_count=10) or [],
        )
    except Exception:
        return None


def get_latest_commit(repo_path: Path) -> Optional["GitCommit"]:  # type: ignore  # noqa: F821
    """
    Get the latest commit information from the git repository.

    Arguments:
        repo_path (Path): The path to the git repository.

    Returns:
        Optional[GitCommit]: The latest commit information if the path is a valid git repository, otherwise None.

    Example:
        >>> latest_commit = get_latest_commit(Path("/path/to/repo"))
        >>> print(latest_commit)
        GitCommit(...)
    """
    from core.models.repo import GitCommit

    if not (repo_path / ".git").exists() or not repo_path.is_dir():
        return None
    try:
        repo = git.Repo(repo_path)
        latest_commit = repo.head.commit
        return GitCommit(
            hash=latest_commit.hexsha[:8],
            message=latest_commit.message.strip(),
            author=str(latest_commit.author),
            date=latest_commit.committed_datetime.isoformat(),
        )
    except Exception:
        return None


def get_all_commits(repo_path: Path, max_count: int = 10) -> Optional[list["GitCommit"]]:  # type: ignore  # noqa: F821
    """Get a list of commits from the git repository."""
    from core.models.repo import GitCommit

    if not (repo_path / ".git").exists() or not repo_path.is_dir():
        return None
    try:
        repo = git.Repo(repo_path)
        commits = []
        for commit in repo.iter_commits(max_count=max_count):
            commits.append(
                GitCommit(
                    hash=commit.hexsha[:8],
                    message=commit.message.strip(),
                    author=str(commit.author),
                    date=commit.committed_datetime.isoformat(),
                )
            )
        return commits
    except Exception:
        return None


def get_repo_name(repo_path: Path) -> Optional[str]:
    """
    Get the repository name from the git repository.

    Arguments:
        repo_path (Path): The path to the git repository.

    Returns:
        Optional[str]: The repository name if the path is a valid git repository, otherwise None.

    Example:
        >>> repo_name = get_repo_name(Path("/tmp/cntrlr"))
        >>> print(repo_name)
        cntrlr
    """
    if not (repo_path / ".git").exists() or not repo_path.is_dir():
        return None
    try:
        repo = git.Repo(repo_path)
        return repo.working_tree_dir.split("/")[-1]
    except Exception:
        return None


def clone_repository(
    repo_url: str, clone_path: Path, branch: Optional[str] = None
) -> Path:
    """
    Clone a git repository to the specified or temporary path.

    Arguments:
        repo_url (str): The URL of the git repository to clone.
        clone_path (Path): The local path to clone the repository into. If None, a temporary directory is used.
        branch: (Optional) The branch to clone. If None, the default branch is used.

    Raises:
        Exception: If cloning fails.

    Returns:
        Path: The path to the cloned repository.

    Example:
        >>> from core.utils import clone_repository
        >>> repo_path = clone_repository("https://Github.com/Willmo103/cntrlr.git", Path("/tmp/cntrlr"))
        >>> print(repo_path)
        C:/tmp/cntrlr
    """
    try:
        if branch:
            git.Repo.clone_from(repo_url, clone_path, branch=branch)
        else:
            git.Repo.clone_from(repo_url, clone_path)
        return clone_path
    except Exception as e:
        raise Exception(f"Failed to clone repository: {e}")


# endregion
# region Time fetchers


def get_time() -> datetime:
    """
    Return the current local time with timezone info.

    Arguments:
        None

    Returns:
        datetime: The current local time with timezone info.

    Example:
        >>> from core.utils import get_time
        >>> ct = get_time()
        >>> print(ct)
        2026-01-26 13:23:40.427374-06:00
    """
    _tz = TZ_OFFSET
    return datetime.now(tz=timezone(timedelta(hours=_tz)))


def get_time_iso(slug=False) -> str:
    """
    Return the current time in ISO 8601 format.

    Arguments:
        slug (bool): If True, return a slug-friendly format (no colons). Defaults to False.

    Returns:
        str: The current time in ISO 8601 format.

    Example:
        >>> from core.utils import get_time_iso
        >>> ct = get_time_iso()
        >>> print(ct)
        2026-01-26T13:25:52
        >>>
        >>> cts = get_time_iso(slug=True)
        >>> print(cts)
        20260126T132636
    """
    _fmt = "%Y%m%dT%H%M%S" if slug else "%Y-%m-%dT%H:%M:%S"
    return get_time().strftime(_fmt)


def timestamp() -> float:
    """
    Return the current timestamp in seconds since the epoch.

    Arguments:
        None

    Returns:
        float: The current timestamp in seconds since the epoch.

    Example:
        >>> from core.utils import timestamp
        >>> ts = timestamp()
        >>> print(ts)
        1769455692.230862
    """
    return get_time().timestamp()


# endregion
