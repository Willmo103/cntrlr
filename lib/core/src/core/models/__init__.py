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
