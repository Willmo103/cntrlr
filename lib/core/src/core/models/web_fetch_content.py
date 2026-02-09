# region Docstring
"""
core.models.web_fetch_content

Persistence and domain models for storing and working with fetched web content.

Overview:
- Provides a SQLAlchemy entity to persist web content fetched from URLs, including
    metadata such as title, summary, tags, and paths to stored artifacts.
- Provides a Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.

Contents:
- SQLAlchemy entities:
    - WebFetchContentEntity:
        Persists fetched web content with URL, UUID, bucket path for raw HTML storage,
        and optional metadata fields (title, summary, descriptions, tags, markdown path).
        Includes DB record timestamps (created_at, updated_at). Provides equality and
        hashing based on UUID, and a .model property to convert to the WebFetchContent
        Pydantic model.

- Pydantic models:
    - WebFetchContent:
        A domain model representing fetched web content. Includes URL, optional UUID,
        title, short/long descriptions, tags, AI-generated summary, markdown path, and
        added/updated timestamps. Provides a JSON-oriented serializer for consistent
        API output with ISO-formatted timestamps.

Design notes:
- .model property on the SQLAlchemy entity provides immediate conversion to the Pydantic
    model for safe I/O layers.
- Pydantic serializers normalize timestamps to ISO 8601 format for consistent API responses.
- New metadata fields (title, summary, markdown_path, etc.) are nullable for backward
    compatibility with existing records.
- UUID-based equality and hashing enables deduplication of fetched content.
"""

# endregion
# region Imports
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_serializer
from sqlalchemy import JSON, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base

# endregion


# region WebFetchContent Model
class WebFetchContentEntity(Base):
    """
    Model representing fetched web content.
    Attributes:
        id (int): Primary key.
        url (str): The URL from which the content was fetched.
        uuid (str): Unique identifier for the fetched content.
        bucket_path (str): The S3 bucket path where the raw HTML is stored.

        # New Fields for Agent Pipeline
        title (str): The extracted title of the page.
        summary (str): AI-generated summary of the content.
        markdown_path (str): S3 path to the converted Markdown.
    """

    __tablename__ = "web_fetch_contents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    uuid: Mapped[str] = mapped_column(String(100), nullable=True)
    bucket_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # New Nullable Fields (Backward compatible)
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    short_description: Mapped[str] = mapped_column(Text, nullable=True)
    long_description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    markdown_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(
        String(30), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        String(30), nullable=True, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<WebFetchContent(id={self.id}, url='{self.url}', uuid='{self.uuid}')>"

    def __hash__(self) -> int:
        return hash(self.uuid)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WebFetchContentEntity):
            return NotImplemented
        return self.uuid == other.uuid

    @property
    def model(self) -> "WebFetchContent":
        return WebFetchContent(
            id=self.id,
            uuid=self.uuid,
            url=self.url,
            title=self.title,
            short_description=self.short_description,
            long_description=self.long_description,
            tags=self.tags,
            summary=self.summary,
            markdown_path=self.markdown_path,
            added_at=self.created_at,
            updated_at=self.updated_at,
        )


# endregion

# region Pydantic Model for WebFetchContent


class WebFetchContent(BaseModel):
    """
    Pydantic model for WebFetchContentEntity.

    Attributes:
        id (Optional[int]): Unique ID of the web fetch content.
        uuid (Optional[str]): Unique identifier for the fetched content.
        url (str): The URL from which the content was fetched.
        title (Optional[str]): The extracted title of the page.
        summary (Optional[str]): AI-generated summary of the content.
        markdown_path (Optional[str]): S3 path to the converted Markdown.
    """

    id: Optional[int] = Field(None, description="Unique ID of the web fetch content")
    uuid: Optional[str] = Field(
        None, max_length=100, description="Unique identifier for the fetched content"
    )
    url: str = Field(
        ..., max_length=500, description="The URL from which the content was fetched"
    )
    title: Optional[str] = Field(
        None, max_length=500, description="The extracted title of the page"
    )
    short_description: Optional[str] = Field(
        None, description="A short description of the content"
    )
    long_description: Optional[str] = Field(
        None, description="A long description of the content"
    )
    tags: Optional[List[str]] = Field(
        [], description="Tags associated with the content"
    )
    summary: Optional[str] = Field(
        None, description="AI-generated summary of the content"
    )
    markdown_path: Optional[str] = Field(
        None, max_length=500, description="S3 path to the converted Markdown"
    )
    added_at: Optional[datetime] = Field(
        None, description="Timestamp when the content was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the content was last updated"
    )

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "id": self.id,
            "uuid": self.uuid,
            "url": self.url,
            "title": self.title,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "tags": self.tags,
            "summary": self.summary,
            "markdown_path": self.markdown_path,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def entity(self) -> WebFetchContentEntity:
        return WebFetchContentEntity(
            id=self.id if self.id is not None else None,
            uuid=self.uuid,
            url=self.url,
            title=self.title,
            short_description=self.short_description,
            long_description=self.long_description,
            tags=self.tags,
            summary=self.summary,
            markdown_path=self.markdown_path,
            created_at=self.added_at,
            updated_at=self.updated_at,
        )

    model_config = ConfigDict(from_attributes=True)


# endregion

__all__ = ["WebFetchContentEntity", "WebFetchContent"]
