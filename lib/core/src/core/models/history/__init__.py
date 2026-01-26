"""
core.models.history
Package initialization for history-related persistence and domain models.
Overview:
- Provides Pydantic models for tracking and persisting clipboard history data.
- Defines entity and model classes for clipboard operations that can be stored
    and retrieved from various persistence backends.
Contents:
- Entity Models:
    - ClipboardHistoryEntity:
        Database/persistence entity representing a single clipboard history record
        with timestamps, content, and metadata for storage operations.
- Domain Models:
    - ClipboardHistory:
        Pydantic model for representing clipboard history with content tracking,
        timestamps, and serialization support for API compatibility.
Design Notes:
- All models follow Pydantic v2 conventions consistent with the core.models.file_system
    base classes.
- Entity models are designed for database persistence while domain models handle
    validation and serialization.
- Exports are organized into __entities__ and __models__ lists for clear separation
    of concerns.
core.models.history package initialization.

"""

from .clipboard_history import ClipboardHistory, ClipboardHistoryEntity  # noqa: F401


__entities__ = ["ClipboardHistoryEntity"]
__models__ = ["ClipboardHistory"]
__all__ = [*__entities__, *__models__]
