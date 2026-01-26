# region Docstring
"""
core.models
Centralized imports for all Pydantic models and SQLAlchemy entities across the application.

Overview:
- Provides a single import point for all domain models, persistence entities, and base classes
    used throughout the core application.
- Organizes models into logical groups: file system models, domain-specific entities,
    and utility models for various application features.
- Maintains separate collections for SQLAlchemy entities (database persistence) and
    Pydantic models (application logic and I/O).

Contents:
- File System Models:
        - Base models for files, directories, and file statistics across platforms
        - Specialized file types (audio, video, image, data, SQLite files)
        - Text file models with line-by-line content parsing
        - Scan result models for file system operations

- Domain Models:
        - Obsidian vault and note management (ObsidianVault, ObsidianNote, ObsidianNoteLine)
        - Git repository scanning and file tracking (Repo, RepoFile)
        - Web content fetching and article processing (Article, WebFetchContent)
        - Note-taking and knowledge management (Note)

- Utility Models:
        - Clipboard history tracking (ClipboardHistory)
        - Text-to-speech history (TTSHistory)
        - File conversion results (ConversionResult)
        - Vector embeddings for semantic search (Embedding)
        - Application logging (LogEntry)
        - Network host discovery (NetworkHost)

Exports:
- entities: List of SQLAlchemy entity class names for database operations
- models: List of Pydantic model class names for application logic
- __all__: Combined export list for comprehensive module access

Design Notes:
- Follows the pattern of separating persistence entities from domain models
- Entity classes handle database operations and relationships
- Pydantic models provide validation, serialization, and business logic
- All imports use noqa: F401 to suppress unused import warnings in this aggregation module
"""
from .article import Article, ArticleEntity  # noqa: F401
from .conversion_result import ConversionResult, ConversionResultEntity  # noqa: F401
from .embedding import Embedding, EmbeddingEntity  # noqa: F401

# region Imports
from .file_system import (  # noqa: F401
    AudioFile,
    AudioFileEntity,
    BaseDirectory,
    BaseFileModel,
    BaseFileStat,
    BaseScanResult,
    BaseTextFile,
    DataFile,
    DataFileEntity,
    FilePath,
    GenericFile,
    ImageFile,
    ImageFileEntity,
    ImageScanResult,
    LinuxFileStat,
    MacOSFileStat,
    SQLiteFile,
    SQLiteFileEntity,
    TextFileLine,
    VideoFile,
    VideoFileEntity,
    VideoScanResult,
    WindowsFileStat,
)
from .history import ClipboardHistory, ClipboardHistoryEntity  # noqa: F401
from .log_entry import LogEntry, LogEntryEntity  # noqa: F401
from .network_host import NetworkHost, NetworkHostEntity  # noqa: F401
from .notes import Note, NoteEntity  # noqa: F401
from .obsidian import (  # noqa: F401
    ObsidianNote,
    ObsidianNoteEntity,
    ObsidianNoteLine,
    ObsidianNoteLineEntity,
    ObsidianScanResult,
    ObsidianVault,
    ObsidianVaultEntity,
)
from .repo import (  # noqa: F401
    GitCommit,
    GitMetadata,
    Repo,
    RepoEntity,
    RepoFile,
    RepoFileEntity,
    RepoFileLineEntity,
    RepoScanResult,
)
from .tts import TTSHistory, TTSHistoryEntity  # noqa: F401
from .web_fetch_content import WebFetchContent, WebFetchContentEntity  # noqa: F401


# endregion

entities = [
    "ArticleEntity",
    "ConversionResultEntity",
    "EmbeddingEntity",
    "LogEntryEntity",
    "NetworkHostEntity",
    "NoteEntity",
    "ObsidianVaultEntity",
    "ObsidianNoteEntity",
    "ObsidianNoteLineEntity",
    "RepoEntity",
    "RepoFileEntity",
    "RepoFileLineEntity",
    "TTSHistoryEntity",
    "WebFetchContentEntity",
]
"""
Entity classes for database persistence.
"""

models = [
    "Article",
    "ConversionResult",
    "Embedding",
    "LogEntry",
    "NetworkHost",
    "Note",
    "ObsidianVault",
    "ObsidianNote",
    "ObsidianNoteLine",
    "Repo",
    "RepoFile",
    "TTSHistory",
    "WebFetchContent",
    "BaseFileStat",
    "MacOSFileStat",
    "LinuxFileStat",
    "WindowsFileStat",
    "GenericFile",
    "AudioFile",
    "DataFile",
    "ImageFile",
    "ImageScanResult",
    "VideoFile",
    "VideoScanResult",
    "SQLiteFile",
    "GitCommit",
    "GitMetadata",
]
"""
Pydantic model classes for application logic and I/O.
"""

__all__ = entities + models
