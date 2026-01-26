# region Docstring
"""
core.models.history.clipboard_history
Persistence and domain models for managing clipboard history entries.
Overview:
- Provides SQLAlchemy entity to persist clipboard history entries with content,
    metadata, and access tracking.
- Provides Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.
Contents:
- SQLAlchemy entities:
    - ClipboardHistoryEntity:
        Stores clipboard history entries including content, content hash for deduplication,
        content type classification, optional file metadata (path, size, MIME type),
        thumbnail data for visual content, and access tracking. Includes helpers for
        equality, hashing, and conversion to a ClipboardHistory Pydantic model via
        the .model property.
- Pydantic models:
    - ClipboardHistory:
        A domain model representing a single clipboard history entry. Includes content
        data, content type classification, optional file metadata, favorite marking,
        access counting, backup status, and timestamp tracking. Provides JSON schema
        examples for API documentation and supports attribute-based instantiation.
Design notes:
- .model property on the SQLAlchemy entity provides immediate conversion to the Pydantic
    model for safe I/O layers.
- content_hash enables efficient deduplication of identical clipboard entries.
- access_count tracks usage frequency for potential sorting/prioritization features.
- is_favorite and backed_up flags support user organization and data persistence workflows.
- Timestamps (timestamp, created_at, updated_at) enable chronological ordering and
    audit trails.
"""
# endregion
# region Imports
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


# endregion
# region SQLAlchemy Model
class ClipboardHistoryEntity(Base):
    """
    Model representing clipboard history entries.
    Attributes:
        id (int): Primary key.
        content (str): The clipboard content.
        content_hash (Optional[str]): Hash of the content for deduplication.
        content_type (str): Type of the content (e.g., text, image).
        file_path (Optional[str]): File path if the content is from a file.
        file_size (Optional[int]): Size of the file content in bytes.
        mime_type (Optional[str]): MIME type of the content.
        thumbnail (Optional[str]): Thumbnail image data for visual content.
        timestamp (datetime): Timestamp when the content was copied.
        is_favorite (bool): Whether the entry is marked as favorite.
        access_count (int): Number of times the entry has been accessed.
        backed_up (bool): Whether the entry has been backed up.
    """

    __tablename__ = "clipboard_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content_hash: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, unique=True
    )
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="text"
    )
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    backed_up: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ClipboardHistory(id={self.id}, content_type='{self.content_type}', timestamp={self.timestamp})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClipboardHistoryEntity):
            return NotImplemented
        return self.id == other.id and self.content_hash == other.content_hash

    def __hash__(self) -> int:
        return hash((self.id, self.content_hash))

    @property
    def model(self) -> "ClipboardHistory":
        return ClipboardHistory(
            id=self.id,
            content=self.content,
            content_hash=self.content_hash,
            content_type=self.content_type,
            file_path=self.file_path,
            file_size=self.file_size,
            mime_type=self.mime_type,
            thumbnail=self.thumbnail,
            timestamp=self.timestamp,
            is_favorite=self.is_favorite,
            access_count=self.access_count,
            backed_up=self.backed_up,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


# endregion
# region Pydantic Model
class ClipboardHistory(BaseModel):
    id: Optional[int] = Field(
        None, description="The unique ID of the clipboard history entry"
    )
    content: str = Field(..., description="The content of the clipboard entry")
    content_hash: Optional[str] = Field(
        None, description="The hash of the clipboard content"
    )
    content_type: str = Field(
        "text", description="The type of content (e.g., text, image)"
    )
    file_path: Optional[str] = Field(
        None, description="The file path if the content is a file"
    )
    file_size: Optional[int] = Field(None, description="The size of the file in bytes")
    mime_type: Optional[str] = Field(None, description="The MIME type of the content")
    thumbnail: Optional[str] = Field(
        None, description="Thumbnail data for image content"
    )
    timestamp: Optional[datetime] = Field(
        None, description="The timestamp of when the entry was created"
    )
    is_favorite: bool = Field(
        False, description="Indicates if the entry is marked as favorite"
    )
    access_count: int = Field(
        0, description="Number of times the entry has been accessed"
    )
    backed_up: bool = Field(
        False, description="Indicates if the entry has been backed up"
    )
    created_at: Optional[datetime] = Field(
        None, description="Timestamp when the entry was created"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the entry was last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "content": "Sample clipboard text",
                    "content_hash": "abc123",
                    "content_type": "text",
                    "file_path": None,
                    "file_size": None,
                    "mime_type": "text/plain",
                    "thumbnail": None,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "is_favorite": True,
                    "access_count": 5,
                    "backed_up": False,
                }
            ]
        },
        from_attributes=True,
    )


# endregion

__all__ = ["ClipboardHistoryEntity", "ClipboardHistory"]
