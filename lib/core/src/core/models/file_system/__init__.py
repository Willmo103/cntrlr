# region Docstring
"""
core.models.file_system
File system models package for representing files, directories, and scan operations.
Overview:
    This package provides Pydantic models and SQLAlchemy entities for representing
    various file types, directories, and file system scan results. It includes
    support for different media types (audio, video, image), data files, SQLite
    databases, and platform-specific file statistics.
Modules:
    - base: Foundational models for file paths, statistics, and generic files.
    - audio_file: Models and entities for audio file representation.
    - data_file: Models and entities for data file representation.
    - image_file: Models and entities for image file representation.
    - video_file: Models and entities for video file representation.
    - sqlite_file: Models and entities for SQLite database file representation.
Entities (SQLAlchemy):
    - AudioFileEntity: Database entity for audio files.
    - DataFileEntity: Database entity for data files.
    - ImageFileEntity: Database entity for image files.
    - VideoFileEntity: Database entity for video files.
    - SQLiteFileEntity: Database entity for SQLite files.
Pydantic Models:
    - FilePath: Represents pathlib.Path attributes with full decomposition.
    - BaseFileStat: Base model for POSIX file statistics.
    - MacOSFileStat: macOS/BSD-specific file statistics.
    - LinuxFileStat: Linux-specific file statistics.
    - WindowsFileStat: Windows-specific file statistics.
    - BaseFileModel: Abstract base for all file representations.
    - GenericFile: Simple file model for unclassified files.
    - TextFileLine: Represents a single line in a text file.
    - BaseTextFile: Text file model with content and line parsing.
    - BaseDirectory: Represents a directory with metadata.
    - BaseScanResult: Base model for file system scan operation results.
    - AudioFile: Pydantic model for audio files.
    - DataFile: Pydantic model for data files.
    - ImageFile: Pydantic model for image files.
    - VideoFile: Pydantic model for video files.
    - SQLiteFile: Pydantic model for SQLite database files.
Exports:
    __entities__: List of all SQLAlchemy entity class names.
    __models__: List of all Pydantic model class names.
    __all__: Combined list of all exported names.
Design Notes:
    - Clear separation between SQLAlchemy entities for persistence and Pydantic
        models for domain representation and validation.
    - Modular structure allows for easy extension with additional file types or
        platform-specific models.
    - Consistent naming conventions and documentation for maintainability.
"""
# endregion
# region Imports

from .audio_file import AudioFile, AudioFileEntity  # noqa: F401
from .base import (  # noqa: F401
    BaseDirectory,
    BaseFileModel,
    BaseFileStat,
    BaseScanResult,
    BaseTextFile,
    FilePath,
    GenericFile,
    LinuxFileStat,
    MacOSFileStat,
    TextFileLine,
    WindowsFileStat,
)
from .data_file import DataFile, DataFileEntity  # noqa: F401
from .image_file import ImageFile, ImageFileEntity, ImageScanResult  # noqa: F401
from .sqlite_file import SQLiteFile, SQLiteFileEntity  # noqa: F401
from .video_file import VideoFile, VideoFileEntity, VideoScanResult  # noqa: F401


# endregion
# region Exports
__all__ = [
    "AudioFileEntity",
    "DataFileEntity",
    "ImageFileEntity",
    "VideoFileEntity",
    "SQLiteFileEntity",
    "AudioFile",
    "DataFile",
    "ImageFile",
    "ImageScanResult",
    "VideoFile",
    "VideoScanResult",
    "SQLiteFile",
    "GenericFile",
    "FilePath",
    "BaseFileStat",
    "MacOSFileStat",
    "LinuxFileStat",
    "WindowsFileStat",
    "BaseFileModel",
    "TextFileLine",
    "BaseTextFile",
    "BaseDirectory",
    "BaseScanResult",
]
# endregion
