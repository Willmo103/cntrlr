"""
core.models.notes
Persistence and domain models for agent notes.
Overview:
- Provides SQLAlchemy entity to persist agent notes with title, content, tags, and timestamps.
- Provides Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.
- Includes YAML front matter generation for Obsidian-compatible note formatting.
Contents:
- SQLAlchemy entities:
    - NoteEntity:
        Persists a single agent note with title, content, tags, and database timestamps.
        Includes helpers for equality, hashing, YAML front matter generation, and conversion
        to a Note Pydantic model via the .model property.
- Pydantic models:
    - Note:
        A domain model representing a single agent note. Includes title, content, optional
        tags, and created/updated timestamps. Provides YAML front matter generation for
        Obsidian-compatible output. Validators ensure tags default to empty list when None.
        Serializers normalize timestamps to ISO 8601 strings.
Design notes:
- .model property on SQLAlchemy entity provides immediate conversion to Pydantic model
    for safe I/O layers.
- YAML front matter generation enables seamless integration with Obsidian and other
    markdown-based note systems.
- Pydantic validators and serializers normalize timestamps (ISO 8601) and ensure
    consistent tag handling (empty list vs None).
- ConfigDict with from_attributes=True enables direct model validation from ORM objects.

"""

# region Imports
from datetime import datetime
from typing import Optional

import yaml
from core.database import Base
from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

# endregion


# region Sqlalchemy Note Model
class NoteEntity(Base):
    """
    Model representing Agent Notes.
    Attributes:
        id (int): Primary key.
        content (str): The content of the note.
        title (str): The title of the note.
        tags (JSON): Tags associated with the note.
        created_at (datetime): Timestamp when the note was created.
        updated_at (datetime): Timestamp when the note was last updated.
    """

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )  # noqa: E501
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=True)

    # timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Notes(id={self.id}, title='{self.title}')>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NoteEntity):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def yaml_front_matter(self) -> str:
        """Generate YAML front matter for the note."""
        front_matter = {
            "title": self.title,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        return "---\n" + yaml.dump(front_matter) + "---\n"

    @property
    def full_content_with_front_matter(self) -> str:
        """Get the full content of the note including YAML front matter."""
        return self.yaml_front_matter + self.content

    @property
    def model(self) -> "Note":
        """Return the Pydantic model representation of the note."""
        return Note.model_validate(
            {
                "id": self.id,
                "title": self.title,
                "content": self.content,
                "tags": self.tags,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )


# endregion

# region Pydantic Note Model


class Note(BaseModel):
    id: Optional[int] = None
    title: str
    content: str
    tags: Optional[list[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @property
    def yaml_front_matter(self) -> str:
        """Generate YAML front matter for the note."""
        front_matter = {
            "title": self.title,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return "---\n" + yaml.dump(front_matter) + "---\n"

    @property
    def full_content_with_front_matter(self) -> str:
        """Get the full content of the note including YAML front matter."""
        return self.yaml_front_matter + self.content

    @field_validator("tags", mode="before")
    def validate_tags(cls, v: Optional[list[str]]) -> list[str]:
        """Ensure tags is always a list, even if None is provided."""
        return v or []

    @field_serializer("tags")
    def serialize_tags(self, v: Optional[list[str]]) -> list[str]:
        """Serialize tags to an empty list if None."""
        return v or []

    @field_serializer("created_at")
    def serialize_created_at(self, v: Optional[datetime]) -> Optional[str]:
        """Serialize created_at to ISO format string."""
        return v.isoformat() if v else None

    @field_serializer("updated_at")
    def serialize_updated_at(self, v: Optional[datetime]) -> Optional[str]:
        """Serialize updated_at to ISO format string."""
        return v.isoformat() if v else None


# endregion


__all__ = ["NoteEntity", "Note"]
