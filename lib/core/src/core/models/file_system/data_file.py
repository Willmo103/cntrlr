# region Docstring
"""
core.models.file_system.data_file

Persistence and domain models for indexing and working with generic data files.

Overview:
- Provides a SQLAlchemy entity to persist data files with path/stat metadata, content,
    and computed columns for efficient querying.
- Provides a Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.

Contents:
- SQLAlchemy entities:
    - DataFileEntity:
        Persists a single data file with path/stat metadata, content, tags, and descriptions.
        Several columns are computed from JSON fields (e.g., filename, extension, size,
        filesystem timestamps). Includes a .model property to convert to the DataFile
        Pydantic model, as well as helper properties for stat_model, path_model, Path,
        and summary. Provides freeze/unfreeze methods to toggle immutability.

- Pydantic models:
    - DataFile:
        A domain model representing a generic data file. Includes discriminator type ("data"),
        optional content, and all common file metadata (path/stat/tags/descriptions).
        Validates that the file path corresponds to a recognized data file type.
        Provides JSON-oriented serialization for consistent API output.

Design notes:
- .model property on the SQLAlchemy entity provides an immediate conversion to the Pydantic
    model for safe I/O layers.
- Computed columns reduce duplication and ensure consistent derivation of metadata from
    JSON fields without requiring application-side recomputation.
- The model_validator ensures only recognized data file types are represented by this model.
- Equality and hashing on the entity are based on id and sha256 for reliable identity checks.
"""
# endregion
# region Imports
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from core.database import Base
from core.models.file_system.base import BaseFileModel, BaseFileStat, FilePath
from core.utils import is_data_file
from pydantic import Field, model_serializer, model_validator
from sqlalchemy import JSON, Computed, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


# endregion
# region Sqlalchemy Model
class DataFileEntity(Base):
    """
    Model representing a text file in the file system.
    Attributes:
        id (str): Primary key.
        sha256 (str): SHA256 hash of the text file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the text file.
        tags (Optional[list[str]]): Tags associated with the text file.
        short_description (Optional[str]): Short description of the text file.
        long_description (Optional[str]): Long description of the text file.
        frozen (bool): Indicates if the file is frozen (immutable).
        content (str): The actual content of the text file.
    """

    __tablename__ = "data_files"

    id: Mapped[str] = mapped_column(primary_key=True)

    # --- COMPUTED METADATA (Matching Pydantic PathModel) ---
    filename: Mapped[str] = mapped_column(
        String(255), Computed("path_json->>'name'", persisted=True), index=True
    )
    extension: Mapped[str] = mapped_column(
        String(20), Computed("path_json->>'suffix'", persisted=True), index=True
    )

    size_bytes: Mapped[int] = mapped_column(
        Integer, Computed("(stat_json->>'st_size')::bigint", persisted=True), index=True
    )

    # Timestamps from Stat
    created_at_fs: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        Computed(
            "to_timestamp((stat_json->>'st_ctime')::double precision)", persisted=True
        ),
    )
    modified_at_fs: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        Computed(
            "to_timestamp((stat_json->>'st_mtime')::double precision)", persisted=True
        ),
    )

    # Standard Columns
    sha256: Mapped[str] = mapped_column(String(64))
    path_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    stat_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frozen: Mapped[bool] = mapped_column(String, default=False, server_default="0")

    # Text file specific column
    content: Mapped[str] = mapped_column(Text)

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<DataFile(id={self.id}, filename={self.filename})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataFileEntity):
            return NotImplemented
        return self.id == other.id and self.sha256 == other.sha256

    def __hash__(self) -> int:
        return hash((self.id, self.sha256))

    @property
    def model(self) -> "DataFile":
        """Return the Pydantic model representation of the data file."""
        return DataFile.model_validate(
            {
                "type": "data",
                "id": self.id,
                "path_json": self.path_json,
                "stat_json": self.stat_json,
                "mime_type": self.mime_type,
                "tags": self.tags,
                "short_description": self.short_description,
                "long_description": self.long_description,
                "frozen": self.frozen,
                "content": self.content,
            }
        )

    @property
    def stat_model(self) -> BaseFileStat:
        """Return the FileStat model representation of the file's stat_json."""
        return BaseFileStat.model_validate(self.stat_json)

    @property
    def path_model(self) -> FilePath:
        """Return the FilePath model representation of the file's path_json."""
        return FilePath.model_validate(self.path_json)

    @property
    def Path(self) -> Path:
        """Return the pathlib.Path representation of the file's full path."""
        return self.path_model.Path

    @property
    def summary(self) -> dict[str, str]:
        """Return a summary dictionary of the DataFileEntity."""
        return {
            "file_id": self.id,
            "path": self.path_model.Path.as_posix(),
            "sha256": self.sha256,
            "mimetype": self.mime_type or "unknown",
            "short_description": self.short_description or "",
            "long_description": self.long_description or "",
            "tags": ", ".join(self.tags) if self.tags else "",
        }

    def freeze(self) -> None:
        """Mark the file as frozen (immutable)."""
        self.frozen = True

    def unfreeze(self) -> None:
        """Mark the file as unfrozen (mutable)."""
        self.frozen = False


# endregion
# region Pydantic Model
class DataFile(BaseFileModel):
    """
    A Pydantic model to represent a generic data file.

    Attributes:
        type (Literal["data"]): The discriminator for data file type.
        sha256 (str): The SHA256 hash of the file.
        stat_json (BaseFileStatModel): The file statistics model.
        path_json (PathModel): The path model of the file.
        mime_type (Optional[str]): The MIME type of the file.
        tags (Optional[list[str]]): A list of tags associated with the file.
        short_description (Optional[str]): A short description of the file.
        long_description (Optional[str]): A long description of the file.
        frozen (bool): Indicates if the file is frozen (immutable).
        content (Optional[str]): The content of the data file as a string.
    """

    type: Literal["data"] = Field("data", const=True)
    content: Optional[str] = Field(
        None, description="The content of the data file as a string"
    )

    @model_validator(mode="after")
    def validate_content_data_type(self) -> "DataFile":
        """
        Validates and converts the content to a string if it's a DataFrame.

        Returns:
            DataFileModel: The validated DataFileModel instance.
        """
        if not is_data_file(self.path_json.Path):
            raise ValueError(
                f"The file at {self.path_json.Path} is not a recognized data file type."
            )

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "content": self.content,
        }


# endregion

__all__ = ["DataFileEntity", "DataFile"]
