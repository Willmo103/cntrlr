from pathlib import Path
import stat
import sys

from core.constants import (
    IMAGE_FORMAT_LIST,
    MARKDOWN_EXTENSIONS,
    MD_XREF,
    VIDEO_FORMAT_LIST,
    DATA_FORMAT_LIST,
)
from core.models.file_system.base import (
    WindowsFileStat,
)
from core.models.file_system.base import BaseFileStat, MacOSFileStat
from core.models.file_system.image_file import ImageFile
from core.models.file_system.video_file import VideoFile
from core.models.file_system.sqlite_file import SQLiteFile
from core.models.file_system.audio_file import AudioFile


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


def get_file_stat_model(file_path: Path) -> "BaseFileStat":  # type: ignore # noqa: F821
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
    from core.models.file_system.base import (
        LinuxFileStat,
    )

    file_stat = stat(file_path)

    system = sys.platform
    if system == "Darwin":
        return MacOSFileStat.model_validate(
            {
                stat_key: getattr(file_stat, stat_key)
                for stat_key in dir(file_stat)
                if not stat_key.startswith("_")
            }
        )
    elif system == "Windows":
        return WindowsFileStat.model_validate(
            {
                stat_key: getattr(file_stat, stat_key)
                for stat_key in dir(file_stat)
                if not stat_key.startswith("_")
            }
        )
    elif system == "Linux":
        return LinuxFileStat.model_validate(
            {
                stat_key: getattr(file_stat, stat_key)
                for stat_key in dir(file_stat)
                if not stat_key.startswith("_")
            }
        )
    else:
        return BaseFileStat.model_validate(
            {
                stat_key: getattr(file_stat, stat_key)
                for stat_key in dir(file_stat)
                if not stat_key.startswith("_")
            }
        )


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
    from core.models.file_system.base import FilePath

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


def get_mime_type(file_path: Path) -> str | None:
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
    import mimetypes

    mime_type, _ = mimetypes.guess_type(file_path.as_posix())
    return mime_type


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
    from core.models.file_system.base import BaseFileModel

    try:
        file_model = BaseFileModel(
            sha256=get_file_sha256(file_path),
            stat_json=get_file_stat_model(file_path),
            path_json=get_path_model(file_path),
            mime_type=get_mime_type(file_path),
            tags=[],  # Initialize with empty tags list
            short_description=None,  # Set default to None
            long_description=None,  # Set default to None
            frozen=False,  # Set default to False
        )
        file_model.populate(file_path)
        return file_model
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
        _base = BaseFileModel_from_Path(file_path)
        img_model = ImageFile.model_validate(_base.model_dump())
        img_model.populate(file_path)
        return img_model
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
        _base = BaseFileModel_from_Path(file_path)
        video_model = VideoFile.model_validate(_base.model_dump())
        video_model.populate(file_path)
        return video_model
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
    from core import SQLiteFile

    try:
        _base = BaseFileModel_from_Path(file_path)
        sqlite_model = SQLiteFile.model_validate(_base.model_dump())
        sqlite_model.populate(file_path)
        return sqlite_model
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
        >>> Error: NotImplementedError("This function is not yet implemented.")
    """
    raise NotImplementedError("This function is not yet implemented.")


# endregion
