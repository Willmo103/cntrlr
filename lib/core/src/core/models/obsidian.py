# region Docstring
"""
core.models.obsidian
Persistence and domain models for indexing and working with Obsidian vaults and notes.

Overview:
- Provides SQLAlchemy entities to persist Obsidian vaults, notes, and extracted non-empty
    note lines in a PostgreSQL database.
- Provides Pydantic models mirroring the persisted entities for safe I/O, validation,
    and serialization, extending base models from core.models.file_system.base.
- Includes database trigger DDL to keep an extracted "lines" table synchronized from
    a note's lines_json payload.

Contents:
- Constants:
    - OBSIDIAN_PARENT_FOLDER_MARKER: Marker directory name (".obsidian") used to identify
        Obsidian vault roots.

- SQLAlchemy Entities:
    - ObsidianNoteLineEntity:
        Stores a single non-empty line from a note in the `obsidian_file_lines` table.
        Links to parent note via `note_id` foreign key. Includes content_hash (MD5) for
        deduplication and indexing. Provides .model property to convert to TextFileLine
        Pydantic model and .dict property for dictionary representation.

    - ObsidianNoteEntity:
        Persists a single Obsidian note in the `obsidian_notes` table with:
            - Computed columns derived from JSON fields (filename, extension, size_bytes,
              created_at_fs, modified_at_fs) using PostgreSQL Computed expressions.
            - Full content and lines_json for text storage.
            - Obsidian-specific fields: vault_path, obsidian_tags, links, properties.
            - Standard metadata: sha256, path_json, stat_json, mime_type, tags, descriptions.
        Includes .model property to convert to ObsidianNote Pydantic model.

    - ObsidianVaultEntity:
        Persists a vault directory in the `vaults` table with path/stat metadata, tags,
        descriptions, and associated notes (vault_notes). Includes .model property to
        convert to ObsidianVault Pydantic model and .notes convenience accessor.

- Trigger DDL:
    - process_obsidian_file_lines() function and trigger_shred_lines trigger:
        A PostgreSQL trigger function and trigger that:
            1) Deletes existing line rows for a note when its lines_json is inserted/updated.
            2) Re-inserts non-empty lines from lines_json into the obsidian_file_lines table
               with line_number, content, and content_hash (MD5).
        Expected lines_json shape:
            { "lines": [ {"content": "string", "line_number": 1}, ... ] }

- Pydantic Models:
    - ObsidianNote (extends BaseFileModel):
        Domain model representing a single Obsidian note. Includes:
            - vault_path: Path relative to vault root.
            - obsidian_tags: List of Obsidian-specific tags (e.g., #tag).
            - links: List of wikilinks to other notes.
            - properties: Frontmatter key-value pairs.
            - added_at/updated_at: Timestamps with ISO 8601 serialization/validation.
        Provides .entity property for conversion to ObsidianNoteEntity.

    - ObsidianNoteLine:
        Represents a single line in a note with:
            - is_empty property: True if content is whitespace only.
            - line_length property: Length of content string.
        Provides JSON serializer and .entity property for ObsidianNoteLineEntity conversion.

    - ObsidianVault (extends BaseDirectory):
        Represents a vault directory with:
            - notes: List of ObsidianNote models.
            - index_json: Parsed vault index data (accepts dict or JSON string).
            - added_at/updated_at: Timestamps with ISO 8601 handling.
        Validators coerce dicts/JSON strings into structured data. Provides .entity property
        for conversion to ObsidianVaultEntity.

    - ObsidianScanResult (extends BaseScanResult):
        Represents the result of scanning a vault with mode="obsidian". Contains:
            - vault_index_json: Optional vault index data.
            - vault_notes: List of discovered ObsidianNote models.
        Includes .notes and .index convenience properties.

Design Notes:
- .model properties on SQLAlchemy entities provide immediate conversion to Pydantic
    models for safe API/I/O layers.
- .entity properties on Pydantic models provide conversion back to SQLAlchemy entities
    for database persistence.
- Pydantic validators and serializers normalize timestamps (ISO 8601) and flexible input
    shapes (dicts vs. JSON strings).
- Computed columns reduce duplication and ensure consistent derivation of metadata from
    JSON fields without requiring application-side recomputation.
- The trigger-based line extraction ensures note content changes reflected in lines_json
    are indexed into a relational structure suitable for fast full-text search.
- All models use Pydantic v2 conventions with field_validator, field_serializer,
    and model_serializer decorators for consistent behavior.
"""

# endregion
# region Imports

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_serializer,
)
from sqlalchemy import (
    DDL,
    JSON,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.base import (
    BaseDirectory,
    BaseFileModel,
    BaseScanResult,
    TextFileLine,
)
from core.database import Base


# endregion
# region Constants
OBSIDIAN_PARENT_FOLDER_MARKER = ".obsidian"
"""CONST str: Marker folder name for Obsidian vaults."""


# endregion
# region SQLAlchemy Models
class ObsidianNoteLineEntity(Base):
    """
    Extracted table representing a single non-empty line of text from a TextFile.
    Populated automatically via Database Triggers.

    Attributes:
        id (int): Primary key.
        note_id (str): Foreign key to the parent TextFile.
        line_number (int): The line number in the original file.
        content (str): The content of the line.
        content_hash (str): SHA256 hash of the line content for deduplication.
    """

    __tablename__ = "obsidian_file_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Link back to the parent file
    note_id: Mapped[str] = mapped_column(
        String, ForeignKey("obsidian_notes.id", ondelete="CASCADE"), index=True
    )
    line_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)

    def __repr__(self):
        return f"<FileLine(note_id={self.note_id}, line={self.line_number})>"

    def __eq__(self, other):
        if not isinstance(other, ObsidianNoteLineEntity):
            return NotImplemented
        return (
            self.note_id == other.note_id
            and self.line_number == other.line_number
            and self.content == other.content
            and self.content_hash == other.content_hash
        )

    def __hash__(self):
        return hash((self.note_id, self.line_number, self.content, self.content_hash))

    @property
    def model(self) -> TextFileLine:
        """Return the Pydantic model representation of the file line."""
        return TextFileLine(
            note_id=self.note_id,
            line_number=self.line_number,
            content=self.content,
            content_hash=self.content_hash,
        )

    @property
    def dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "note_id": self.note_id,
            "line_number": self.line_number,
            "content": self.content,
            "content_hash": self.content_hash,
        }


class ObsidianNoteEntity(Base):
    """
    Model representing a text file in the file system.

    Attributes:
        id (str): Primary key.
        vault_id (int): Foreign key to the associated scan result.
        sha256 (str): SHA256 hash of the image file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the image file.
        tags (Optional[list[str]]): Tags associated with the image file.
        short_description (Optional[str]): Short description of the image file.
        long_description (Optional[str]): Long description of the image file.
        frozen (bool): Indicates if the file is frozen (immutable).
        content (str): The actual content of the text file.
        lines_json (Dict[str, Any]): JSON representation of the lines in the text file.
        obsidian_path (Optional[str]): The Obsidian-specific path of the file within the vault.
        obsidian_tags (Optional[list[str]]): Obsidian-specific tags associated with the file.
        updated_at (datetime): Timestamp when the record was last updated.
        created_at (datetime): Timestamp when the record was created.
    """

    __tablename__ = "obsidian_notes"

    id: Mapped[str] = mapped_column(primary_key=True)
    vault_id: Mapped[int] = mapped_column(ForeignKey("vaults.id"), index=True)

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

    # --- Standard Columns ---
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    path_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    stat_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, default=None)
    short_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    long_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    # TextFile specific columns
    content: Mapped[str] = mapped_column(Text, nullable=True)
    lines_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=True, default=dict
    )
    # Obsidian specific columns
    vault_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    obsidian_tags: Mapped[Optional[list[str]]] = mapped_column(
        JSON, default=[], nullable=True
    )
    links: Mapped[Optional[list[str]]] = mapped_column(JSON, default=[], nullable=True)
    properties: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON, default={}, nullable=True
    )

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<TextFile(id={self.id}, sha256='{self.sha256}')>"  # noqa: E501

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ObsidianNoteEntity):
            return NotImplemented

        return self.sha256 == other.sha256

    def __hash__(self) -> int:
        return hash(self.sha256)

    @property
    def model(self) -> "ObsidianNote":
        """Return the Pydantic model representation of the Obsidian file."""
        return ObsidianNote.model_validate(
            {
                "id": self.id,
                "vault_id": self.vault_id,
                "path_json": self.path_json,
                "stat_json": self.stat_json,
                "mime_type": self.mime_type,
                "tags": self.tags,
                "short_description": self.short_description,
                "long_description": self.long_description,
                "frozen": self.frozen,
                "content": self.content,
                "lines_json": self.lines_json,
                "vault_path": self.vault_path,
                "obsidian_tags": self.obsidian_tags,
                "links": self.links,
                "properties": self.properties,
            }
        )

    @property
    def dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vault_id": self.vault_id,
            "path_json": self.path_json,
            "stat_json": self.stat_json,
            "mime_type": self.mime_type,
            "tags": self.tags,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "frozen": self.frozen,
            "content": self.content,
            "lines_json": self.lines_json,
            "vault_path": self.vault_path,
            "obsidian_tags": self.obsidian_tags,
            "links": self.links,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# --- TRIGGER LOGIC FOR FileLinesModel ---
# Expects JSON: { "lines": [ {"content": "...", "line_number": 1}, ... ] }


note_shred_lines_func = DDL(
    """
CREATE OR REPLACE FUNCTION process_obsidian_file_lines()
RETURNS TRIGGER AS $$
DECLARE
    line_obj jsonb;
BEGIN
    -- 1. Clear existing lines
    DELETE FROM obsidian_file_lines WHERE file_id = NEW.id;

    -- 2. Insert new lines
    -- Cast to JSONB for better iteration if column is JSON
    IF NEW.lines_json::jsonb -> 'lines' IS NOT NULL THEN
        FOR line_obj IN SELECT * FROM jsonb_array_elements(NEW.lines_json::jsonb -> 'lines')
        LOOP
            -- Check content is not empty string
            IF length(trim(line_obj->>'content')) > 0 THEN
                INSERT INTO obsidian_file_lines (file_id, line_number, content, content_hash)
                VALUES (
                    NEW.id,
                    (line_obj->>'line_number')::int,
                    line_obj->>'content',
                    md5(line_obj->>'content')
                );
            END IF;
        END LOOP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)
note_trigger_setup = DDL(
    """
CREATE TRIGGER trigger_shred_lines
AFTER INSERT OR UPDATE OF lines_json ON obsidian_files
FOR EACH ROW EXECUTE FUNCTION process_obsidian_file_lines();
"""
)
event.listen(
    ObsidianNoteEntity.__table__, "after_create", note_shred_lines_func
)  # noqa
event.listen(ObsidianNoteEntity.__table__, "after_create", note_trigger_setup)  # noqa


class ObsidianVaultEntity(Base):
    """
    Model representing a text file in the file system.

    Attributes:
        id (str): Primary key.
        vault_id (int): Foreign key to the associated scan result.
        sha256 (str): SHA256 hash of the image file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the image file.
        tags (Optional[list[str]]): Tags associated with the image file.
        short_description (Optional[str]): Short description of the image file.
        long_description (Optional[str]): Long description of the image file.
        frozen (bool): Indicates if the file is frozen (immutable).
        files (list[ObsidianFile_Table]): List of files in the vault.
        updated_at (datetime): Timestamp when the record was last updated.
        created_at (datetime): Timestamp when the record was created.
    """

    __tablename__ = "vaults"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    path_json: Mapped[dict] = mapped_column(String, nullable=False)
    stat_json: Mapped[dict] = mapped_column(String, nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frozen: Mapped[bool] = mapped_column(String, default=False, server_default="0")

    # Vault specific columns
    vault_notes: Mapped[Optional[list[ObsidianNoteEntity]]] = mapped_column(
        String, nullable=True
    )

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(
        String(30), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        String(30), nullable=True, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ObsidianVault(id={self.id}, path='{self.path_json.get('full_path', '')}')>"

    @property
    def notes(self) -> Optional[list["ObsidianNote"]]:
        if self.vault_notes:
            return [file.model for file in self.vault_notes]
        return None

    @property
    def model(self) -> "ObsidianVault":
        return ObsidianVault(
            id=self.id,
            path=self.path_json,
            stat=self.stat_json,
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @property
    def dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path_json": self.path_json,
            "stat_json": self.stat_json,
            "tags": self.tags,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "frozen": self.frozen,
            "vault_notes": (
                [note.dict for note in self.vault_notes] if self.vault_notes else None
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# endregion
# region Pydantic Models


class ObsidianNote(BaseFileModel):
    """
    A Pydantic model to represent an Obsidian file.

    Attributes:
        id: Optional[str]: The unique identifier of the file.
        sha256: Optional[str]: The SHA256 hash of the file.
        stat_json: Optional[str]: The file statistics in JSON format.
        path_json: Optional[str]: The file path in JSON format.
        mime_type: Optional[str]: The MIME type of the file.
        tags: Optional[List[str]]: Tags associated with the file.
        short_description: Optional[str]: A short description of the file.
        long_description: Optional[str]: A long description of the file.
        frozen: Optional[bool]: Indicates if the file is frozen (immutable).
        content: Optional[str]: The content of the text file.
        lines_json: Optional[str]: The lines of the text file in JSON format.
        vault_path (str): The path of the file within the Obsidian vault.
        obsidian_tags (list[str]): List of Obsidian-specific tags found in the file
        links (list[str]): List of links to other notes within the Obsidian vault.
        properties (dict[str, str]): Key-value pairs of Obsidian-specific properties from the
            file's frontmatter.
    """

    vault_path: str = Field(
        ...,
        description="The path of the file within the Obsidian vault",
    )
    obsidian_tags: list[str] = Field(
        default=[],
        description="List of Obsidian-specific tags found in the file",
    )
    links: list[str] = Field(
        default=[],
        description="List of links to other notes within the Obsidian vault",
    )
    properties: dict[str, str] = Field(
        default={},
        description="Key-value pairs of Obsidian-specific properties from the file's frontmatter",
    )
    added_at: Optional[datetime] = Field(
        None, description="Timestamp when the Obsidian note was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the Obsidian note was last updated"
    )

    @field_serializer("added_at")
    def serialize_added_at(self, v: Optional[datetime]) -> Optional[str]:
        if v:
            return v.isoformat()
        return None

    @field_serializer("updated_at")
    def serialize_updated_at(self, v: Optional[datetime]) -> Optional[str]:
        if v:
            return v.isoformat()
        return None

    @field_validator("added_at", mode="before")
    def validate_added_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @field_validator("updated_at", mode="before")
    def validate_updated_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @property
    def entity(self) -> ObsidianNoteEntity:
        return ObsidianNoteEntity(
            id=self.id if self.id is not None else None,
            vault_path=self.vault_path,
            obsidian_tags=self.obsidian_tags,
            links=self.links,
            properties=self.properties,
        )

    def _parse_obsidian_tags(self) -> List[str]:
        """Parse and return Obsidian-specific tags from the content."""
        if not self.content:
            return []
        tags = set()
        for line in self.content.splitlines():
            words = line.split()
            for word in words:
                if word.startswith("#") and len(word) > 1:
                    tag = word[1:].split("/")[0]  # Handle nested tags
                    tags.add(tag)
        return list(tags)

    def _parse_links(self) -> List[str]:
        """Parse and return Obsidian wikilinks from the content."""
        if not self.content:
            return []
        links = set()
        import re

        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, self.content)
        for match in matches:
            link = match.split("|")[0]  # Handle display text
            links.add(link)
        return list(links)

    def _parse_properties(self) -> Dict[str, str]:
        """Parse and return Obsidian frontmatter properties from the content."""
        if not self.content:
            return {}
        properties = {}
        lines = self.content.splitlines()
        if lines and lines[0].strip() == "---":
            i = 1
            while i < len(lines):
                line = lines[i].strip()
                if line == "---":
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    properties[key.strip()] = value.strip()
                i += 1
        return properties

    @classmethod
    def populate(cls, file_path: Path, vault_root: Path) -> "ObsidianNote":
        instance = super().populate(file_path)
        # Obsidian-specific population logic can be added here if needed
        instance.vault_path = str(file_path.relative_to(vault_root))
        obsidian_tags = cls._parse_obsidian_tags(instance)
        links = cls._parse_links(instance)
        properties = cls._parse_properties(instance)
        instance.obsidian_tags = obsidian_tags
        instance.links = links
        instance.properties = properties
        return instance


class ObsidianNoteLine(BaseModel):
    """
    A Pydantic model to represent a line in an Obsidian note.

    Attributes:
        note_id (str): The ID of the Obsidian note.
        content (str): The content of the line.
        line_number (Optional[int]): The line number in the note.
    """

    id: Optional[int] = None
    note_id: str = Field(..., description="The ID of the Obsidian note")
    content: str = Field(..., description="The content of the line")
    line_number: Optional[int] = Field(None, description="The line number in the note")

    @property
    def is_empty(self) -> bool:
        """Check if the line is empty or consists only of whitespace."""
        return self.content.strip() == ""

    @property
    def line_length(self) -> int:
        """Returns the length of the line content."""
        return len(self.content)

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "id": self.id if self.id is not None else None,
            "note_id": self.note_id,
            "content": self.content,
            "line_number": self.line_number,
        }

    @property
    def entity(self) -> ObsidianNoteLineEntity:
        return ObsidianNoteLineEntity(
            note_id=self.note_id,
            line_number=self.line_number if self.line_number is not None else 0,
            content=self.content,
            content_hash="",  # Content hash can be computed as needed
        )


class ObsidianVault(BaseDirectory):
    """
    A Pydantic model to represent an Obsidian vault directory.

    Attributes:
        stat_json (BaseFileStat): The file statistics model.
        path_json (FilePath): The path model of the vault directory.
        tags (Optional[list[str]]): A list of tags associated with the vault.
        short_description (Optional[str]): A short description of the vault.
        long_description (Optional[str]): A long description of the vault.
        frozen (bool): Indicates if the vault is frozen (immutable).
        index_json (Optional[dict[str, Any]]): The index of the vault in JSON format.
        notes (List[ObsidianNote]): List of Obsidian notes in the vault.
    """

    notes: List[ObsidianNote] = Field(
        default=[],
        description="List of Obsidian notes in the vault",
    )
    index_json: Optional[dict[str, Any]] = Field(
        None,
        description="The index of the vault in JSON format",
    )
    added_at: Optional[datetime] = Field(
        None, description="Timestamp when the Obsidian vault was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the Obsidian vault was last updated"
    )

    @field_serializer("added_at")
    def serialize_added_at(self, v: Optional[datetime]) -> Optional[str]:
        if v:
            return v.isoformat()
        return None

    @field_serializer("updated_at")
    def serialize_updated_at(self, v: Optional[datetime]) -> Optional[str]:
        if v:
            return v.isoformat()
        return None

    @field_validator("added_at", mode="before")
    def validate_added_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @field_validator("updated_at", mode="before")
    def validate_updated_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @field_validator("notes", mode="before")
    def validate_notes(
        cls, v: Union[List[ObsidianNote], List[dict[str, Any]]]
    ) -> List[ObsidianNote]:
        if all(isinstance(item, dict) for item in v):
            return [ObsidianNote.model_validate(item) for item in v]
        return v

    @field_validator("index_json", mode="before")
    def validate_index_json(
        cls, v: Union[str, dict[str, Any], None]
    ) -> Optional[dict[str, Any]]:
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string for index_json: {e}")
        elif isinstance(v, dict):
            return v

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "notes": [note.model_dump() for note in self.notes],
            "index_json": (json.dumps(self.index_json) if self.index_json else None),
            "added_at": self.serialize_added_at(self.added_at),
            "updated_at": self.serialize_updated_at(self.updated_at),
        }

    @property
    def entity(self) -> ObsidianVaultEntity:
        return ObsidianVaultEntity(
            id=self.id if self.id is not None else None,
            path_json=self.path.dict(),
            stat_json=self.stat.dict(),
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            vault_notes=[note.entity for note in self.notes],
        )


# endregion
# region Scan Result Model


class ObsidianScanResult(BaseScanResult):
    """
    A Pydantic model to represent the result of an Obsidian vault scan.

    Attributes:
        id (Optional[int]): The unique identifier of the scan result.
        root (str): The root path of the scanned Obsidian vault.
        mode (Literal["obsidian"]): The scanning mode used.
        started_at (Optional[str]): The timestamp when the scan started.
        ended_at (Optional[str]): The timestamp when the scan ended.
        vault_index_json (Optional[dict[str, Any]]): The Obsidian vault index JSON data from the
            `.obsidian/index.json` file.
        vault_notes (List[ObsidianNote]): List of text files found during the scan.
    """

    mode: Literal["obsidian"] = "obsidian"
    vault_index_json: Optional[dict[str, Any]] = Field(
        None,
        description="The Obsidian vault index JSON data from the `.obsidian/index.json` file",
    )
    vault_notes: List["ObsidianNote"] = Field(
        default=[],
        description="List of text files found during the scan",
    )

    @field_validator("vault_notes", mode="before")
    def validate_files(
        cls, v: Union[List["ObsidianNote"], List[dict[str, Any]]]
    ) -> List["ObsidianNote"]:
        if all(isinstance(item, dict) for item in v):
            return [ObsidianNote.model_validate(item) for item in v]
        return v

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "vault_index_json": (
                json.dumps(self.vault_index_json) if self.vault_index_json else None
            ),
            "vault_notes": [file.model_dump() for file in self.vault_notes],
        }

    @property
    def notes(self) -> List["ObsidianNote"]:
        return self.vault_notes

    @property
    def index(self) -> Optional[dict[str, Any]]:
        return self.vault_index_json


# endregion

__all__ = [
    "ObsidianNoteEntity",
    "ObsidianVaultEntity",
    "ObsidianNote",
    "ObsidianVault",
    "ObsidianNoteLine",
    "ObsidianScanResult",
]
