# region Docstring
"""
core.models.file_system.sqlite_file

Persistence and domain models for indexing and working with SQLite database files.

Overview:
- Provides a SQLAlchemy entity to persist SQLite file metadata, schema, and table listings.
- Provides a Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.

Contents:
- SQLAlchemy entities:
    - SQLiteFileEntity:
        Persists a single SQLite database file with path/stat metadata, SHA256 hash,
        schema (DDL), and table names. Several columns are computed from JSON fields
        (e.g., filename, extension, size). Includes a .model property to convert to
        the SQLiteFile Pydantic model, as well as .stat_model, .path_model, .Path,
        and .summary convenience accessors. Supports freeze/unfreeze for immutability.

- Pydantic models:
    - SQLiteFile:
        A domain model representing a SQLite database file. Extends BaseFileModel with
        SQLite-specific attributes: tables (list of table names) and schema (DDL string).
        Includes validators and serializers for consistent API output.

Design notes:
- .model property on the SQLAlchemy entity provides immediate conversion to the Pydantic
    model for safe I/O layers.
- Computed columns reduce duplication and ensure consistent derivation of metadata from
    JSON fields without requiring application-side recomputation.
- Pydantic validators ensure type safety for SQLite-specific fields (e.g., tables list).
"""
# endregion
# region Imports
from datetime import datetime
from pathlib import Path
from typing import Any, List, Literal, Optional

from pydantic import ConfigDict, field_validator, model_serializer
from sqlalchemy import Computed, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core import SQLiteFile
from core.database import Base
from core.models.file_system.base import BaseFileModel, BaseFileStat, FilePath


# endregion
# region Sqlalchemy Model
class SQLiteFileEntity(Base):
    """
    Model representing a SQLite file in the file system.

    Attributes:
        id (str): Primary key.
        sha256 (str): SHA256 hash of the SQLite file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the SQLite file.
        tags (Optional[list[str]]): Tags associated with the SQLite file.
        short_description (Optional[str]): Short description of the SQLite file.
        long_description (Optional[str]): Long description of the SQLite file.
        frozen (bool): Indicates if the file is frozen (immutable).
        schema (str): The database schema in SLQ DDL format.
        tables (List[str]): List of table names in the SQLite database.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "sqlite_files"

    id: Mapped[str] = mapped_column(primary_key=True)

    # --- COMPUTED METADATA ---
    filename: Mapped[str] = mapped_column(
        String(255), Computed("path_json->>'name'", persisted=True), index=True
    )
    extension: Mapped[str] = mapped_column(
        String(20), Computed("path_json->>'suffix'", persisted=True), index=True
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer, Computed("(stat_json->>'st_size')::bigint", persisted=True), index=True
    )

    # Base File Columns
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    path_json: Mapped[dict] = mapped_column(String, nullable=False)
    stat_json: Mapped[dict] = mapped_column(String, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frozen: Mapped[bool] = mapped_column(String, default=False, server_default="0")

    # SQLite specific columns
    schema: Mapped[str] = mapped_column(Text, nullable=False)
    tables: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<SQLiteFile_Table(id={self.id}, filename={self.filename}, size_bytes={self.size_bytes})>"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SQLiteFileEntity):
            return NotImplemented
        return (
            self.id == other.id
            and self.scan_id == other.scan_id
            and self.schema == other.schema
            and self.tables == other.tables
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.scan_id,
                self.schema,
                tuple(self.tables) if self.tables else None,
            )
        )

    @property
    def model(self) -> SQLiteFile:
        """Return the Pydantic model representation of the SQLite file."""
        return SQLiteFile.model_validate(
            {
                "type": "sqlite",
                "id": self.id,
                "path_json": self.path_json,
                "stat_json": self.stat_json,
                "mime_type": self.mime_type,
                "tags": self.tags,
                "short_description": self.short_description,
                "long_description": self.long_description,
                "frozen": self.frozen,
                "schema": self.schema,
                "tables": self.tables,
            }
        )

    @property
    def dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the SQLiteFileEntity."""
        return {
            "id": self.id,
            "sha256": self.sha256,
            "path_json": self.path_json,
            "stat_json": self.stat_json,
            "mime_type": self.mime_type,
            "tags": self.tags,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "frozen": self.frozen,
            "schema": self.schema,
            "tables": self.tables,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

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
# region Pydantic Model for SQLiteFile
class SQLiteFile(BaseFileModel):
    """
    A Pydantic model to represent a SQLite database file.

    Attributes:
        type (Literal["sqlite"]): The discriminator for SQLite file type.
        sha256 (str): The SHA256 hash of the file.
        stat_json (BaseFileStatModel): The file statistics model.
        path_json (PathModel): The path model of the file.
        mime_type (Optional[str]): The MIME type of the file.
        tags (Optional[list[str]]): A list of tags associated with the file.
        short_description (Optional[str]): A short description of the file.
        long_description (Optional[str]): A long description of the file.
        frozen (bool): Indicates if the file is frozen (immutable).
        tables (Optional[List[str]]): List of table names in the database.
        schema (Optional[str]): The database schema as a string.
    """

    type: Literal["sqlite"] = "sqlite"
    tables: Optional[List[str]] = None
    schema: Optional[str] = None

    @classmethod
    def populate(cls, file_path: Path) -> "SQLiteFile":
        super().populate(file_path)
        # SQLite-specific population logic can be added here if needed
        cls.content = file_path.read_text(encoding="utf-8", errors="ignore")
        return cls

    @model_serializer("json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "tables": self.tables,
            "schema": self.schema,
        }

    @field_validator("tables", mode="before")
    def validate_tables(cls, v):
        """
        Validator for 'tables' field to ensure it is a list of strings.
        """
        if v is None:
            return v
        if not isinstance(v, list) or not all(isinstance(item, str) for item in v):
            raise ValueError("tables must be a list of strings")
        return v

    model_config = ConfigDict(
        **BaseFileModel.model_config,
    )


# endregion

__all__ = ["SQLiteFileEntity", "SQLiteFile"]
