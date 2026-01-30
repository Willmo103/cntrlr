# region Docstring
"""
core.models.repo
Persistence and domain models for indexing and working with Git repositories and their files.
Overview:
- Provides SQLAlchemy entities to persist Git repositories, repository files, and extracted
    non-empty file lines.
- Provides Pydantic models mirroring the persisted entities for safe I/O, validation,
    and serialization.
- Includes database trigger DDL to keep an extracted "lines" table synchronized from
    a file's lines_json payload.
Contents:
- Pydantic models for Git Metadata:
    - GitCommit:
        Schema for git commit information including hash, message, author, and date.
    - GitMetadata:
        Schema for git repository metadata including remotes, branches, latest commit,
        uncommitted changes, untracked files, and commit history.
- SQLAlchemy entities:
    - RepoEntity:
        Persists a repository directory with path/stat metadata, type (local or cloned),
        URL, Git metadata, and timestamps. Includes a .name property for convenience.
    - RepoFileEntity:
        Persists a single file in a repository with path/stat metadata, content, tags,
        descriptions, and JSON lines. Several columns are computed from JSON fields
        (e.g., filename, extension, size, filesystem timestamps). Includes a .model
        property to convert to the RepoFile Pydantic model.
    - RepoFileLineEntity:
        Stores a single non-empty line from a repository file. Computed content_hash
        (MD5) aids deduplication and indexing. Includes helpers for equality, hashing,
        and conversion to a TextFileLine Pydantic model.
- Trigger DDL:
    - process_repo_file_lines() and repo_trigger_shred_lines:
        A PostgreSQL trigger function and trigger that:
            1) Deletes existing line rows for a file when its lines_json is inserted/updated.
            2) Re-inserts non-empty lines from lines_json into the lines table with line_number,
                 content, and content_hash.
        Expected lines_json shape:
                "lines": [
                    {"content": "string", "line_number": 1},
                    ...
                ]
- Pydantic models:
    - RepoFile:
        A domain model representing a single file in a repository. Extends BaseTextFile
        with repo_path (relative path within repository) and repo_id fields.
    - Repo:
        Represents a repository directory with type (local/cloned), optional URL, list of
        RepoFile items, Git metadata, and last_seen timestamp. Validators ensure type
        consistency and URL format. Includes a .docs property to filter documentation files.
    - RepoScanResult:
        Represents the result of scanning a repository in mode="git-local" or "git-cloned".
        Carries the repository model containing details about the scanned repository.
        Includes validators and serialization helpers.
Design notes:
- .model properties on SQLAlchemy entities provide an immediate conversion to Pydantic
    models for safe I/O layers.
- Pydantic validators normalize flexible input shapes (dicts vs. model instances) and
    enforce type constraints.
- Computed columns reduce duplication and ensure consistent derivation of metadata from
    JSON fields without requiring application-side recomputation.
- The trigger-based line extraction ensures file content changes reflected in lines_json
    are indexed into a relational structure suitable for fast search.
"""

# endregion
# region Imports
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import git
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer
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
    BaseScanResult,
    BaseTextFile,
    TextFileLine,
)
from core.config.base import REMOTES_DIR
from core.database import Base
from core.models.file_system import BaseDirectory
from core.utils import (
    get_git_metadata,
    is_binary_file,
    is_image_file,
    is_video_file,
)


# endregion
# region Pydantic Models for Git Metadata


class GitCommit(BaseModel):
    """Schema for git commit information."""

    hash: str = Field(..., description="Commit hash")
    message: str = Field(..., description="Commit message")
    author: str = Field(..., description="Author of the commit")
    date: str = Field(..., description="Date of the commit")


class GitMetadata(BaseModel):
    """Schema for git repository metadata."""

    remotes: Dict[str, str] = Field(..., description="Git remotes")
    current_branch: str = Field(..., description="Current branch name")
    branches: List[str] = Field(..., description="List of all branches")
    latest_commit: GitCommit = Field(
        ..., description="Latest commit information"
    )  # noqa: E501
    uncommitted_changes: bool = Field(
        ..., description="Whether there are uncommitted changes"
    )
    untracked_files: int = Field(..., description="Number of untracked files")
    commit_history: Optional[List[GitCommit]] = Field(
        [], description="List of recent commits"
    )


# endregion
# region SQLAlchemy Models and Pydantic Models for Repos


class RepoEntity(Base):
    """
    Base model for a repository.

    Attributes:
        id (int): Primary key.
        stat_json (dict): JSON field storing file statistics.
        path_json (dict): JSON field storing path information.
        tags (Optional[list[str]]): List of tags associated with the repository.
        short_description (Optional[str]): Short description of the repository.
        long_description (Optional[str]): Long description of the repository.
        frozen (bool): Indicates if the repository is frozen (immutable).
        repo_type (Literal["git-local", "git-cloned"]): Type of the repository.
        url (Optional[str]): URL of the repository.
        git_metadata (Optional[dict]): JSON field storing Git-specific metadata.
        last_seen (Optional[datetime]): Timestamp when the repository was last seen.
        created_at (datetime): Timestamp when the record was created.
        updated_at (Optional[datetime]): Timestamp when the record was last updated.
    """

    # base Directory fields
    __tablename__ = "repos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_json: Mapped[dict] = mapped_column(String, nullable=False)
    path_json: Mapped[dict] = mapped_column(String, nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frozeen: Mapped[bool] = mapped_column(String, default=False, server_default="0")

    # repo-specific fields
    repo_type: Mapped[Literal["git-local", "git-cloned"]] = mapped_column(
        String(20), nullable=False
    )
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    git_metadata: Mapped[Optional[dict]] = mapped_column(String, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(String(30), nullable=True)

    files: Mapped[List["RepoFileEntity"]] = Computed(
        "SELECT * FROM repo_files WHERE repo_id = id", persisted=False
    )

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(String(30), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(String(30), nullable=True)

    @property
    def name(self) -> str:
        return self.path_json.get("name", "")

    def __repr__(self) -> str:
        return f"<Repo(id={self.id}, path='{self.path_json.get('full_path', '')}')>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RepoEntity):
            return NotImplemented

        return self.git_metadata == other.git_metadata

    def __hash__(self) -> int:
        return hash(self.git_metadata)

    @property
    def model(self) -> "Repo":
        return Repo(
            id=self.id,
            stat_json=self.stat_json,
            path_json=self.path_json,
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            repo_type=self.repo_type,
            url=self.url,
            git_metadata=(
                GitMetadata.model_validate(self.git_metadata)
                if self.git_metadata
                else None
            ),
            last_seen=self.last_seen,
        )


class RepoFileEntity(Base):
    """
    Model representing a text file in a repository.

    Attributes:
        id (str): Primary key.
        scan_id (int): Foreign key to the associated scan result.
        sha256 (str): SHA256 hash of the image file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the image file.
        tags (Optional[list[str]]): Tags associated with the image file.
        short_description (Optional[str]): Short description of the image file.
        long_description (Optional[str]): Long description of the image file.
        frozen (bool): Indicates if the file is frozen (immutable).
        content (str): The actual content of the text file.
        repo_path (Optional[str]): The relative path of the file within the repository.
        lines_json (Dict[str, Any]): JSON representation of the lines in the text file.
        updated_at (datetime): Timestamp when the record was last updated.
        created_at (datetime): Timestamp when the record was created.
    """

    __tablename__ = "repo_files"

    id: Mapped[str] = mapped_column(primary_key=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("repos.id"), index=True)

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

    # Inherent Text File Columns
    content: Mapped[str] = mapped_column(Text, nullable=True)
    lines_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=True, default=dict
    )

    # RepoFile Specific Columns
    repo_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # relative path in repo

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<TextFile(id={self.id}, sha256='{self.sha256}')>"  # noqa: E501

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RepoFileEntity):
            return NotImplemented

        return self.sha256 == other.sha256

    def __hash__(self) -> int:
        return hash(self.sha256)

    @property
    def model(self):
        return RepoFile.model_validate(**self.__dict__)


# region DDL and Trigger for RepoFileLineEntity
# --- TRIGGER LOGIC FOR FileLinesModel ---
# Expects JSON: { "lines": [ {"content": "...", "line_number": 1}, ... ] }

repo_shred_lines_func = DDL(
    """
CREATE OR REPLACE FUNCTION process_repo_file_lines()
RETURNS TRIGGER AS $$
DECLARE
    line_obj jsonb;
BEGIN
    -- 1. Clear existing lines
    DELETE FROM repo_file_lines WHERE file_id = NEW.id;

    -- 2. Insert new lines
    -- Cast to JSONB for better iteration if column is JSON
    IF NEW.lines_json::jsonb -> 'lines' IS NOT NULL THEN
        FOR line_obj IN SELECT * FROM jsonb_array_elements(NEW.lines_json::jsonb -> 'lines')
        LOOP
            -- Check content is not empty string
            IF length(trim(line_obj->>'content')) > 0 THEN
                INSERT INTO repo_file_lines (file_id, line_number, content, content_hash)
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
setup_repo_file_lines_trigger = DDL(
    """
CREATE TRIGGER repo_trigger_shred_lines
AFTER INSERT OR UPDATE OF lines_json ON repo_files
FOR EACH ROW EXECUTE FUNCTION process_repo_file_lines();
"""
)


event.listen(RepoFileEntity.__table__, "after_create", repo_shred_lines_func)  # noqa
event.listen(
    RepoFileEntity.__table__, "after_create", setup_repo_file_lines_trigger
)  # noqa
# endregion


class RepoFileLineEntity(Base):
    """
    Extracted table representing a single non-empty line of text from a TextFile.
    Populated automatically via Database Triggers.

    Attributes:
        id (int): Primary key.
        file_id (str): Foreign key to the parent TextFile.
        line_number (int): The line number in the original file.
        content (str): The content of the line.
        content_hash (str): SHA256 hash of the line content for deduplication.
    """

    __tablename__ = "repo_file_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Link back to the parent file
    file_id: Mapped[str] = mapped_column(
        String, ForeignKey("repo_files.id", ondelete="CASCADE"), index=True
    )
    line_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)

    @property
    def model(self) -> TextFileLine:
        """Return the Pydantic model representation of the file line."""
        return TextFileLine(
            file_id=self.file_id,
            line_number=self.line_number,
            content=self.content,
            content_hash=self.content_hash,
        )

    def __repr__(self):
        return f"<FileLine(file_id={self.file_id}, line={self.line_number})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RepoFileLineEntity):
            return NotImplemented

        return (
            self.file_id == other.file_id
            and self.line_number == other.line_number
            and self.content_hash == other.content_hash
        )

    def __hash__(self) -> int:
        return hash((self.file_id, self.line_number, self.content_hash))


# endregion
# region Pydantic Models for Repos


class RepoFile(BaseTextFile):
    """
    A Pydantic model to represent a file in a repository.

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
        repo_path (Optional[str]): The file's relative path within the repository.
        repo_id (Optional[str]): The ID of the repository.

    """

    repo_path: Optional[str] = Field(
        None, description="The file's relative path within the repository"
    )
    repo_id: Optional[str] = Field(None, description="The ID of the repository")

    @property
    def entity(self) -> RepoFileEntity:
        """Return the SQLAlchemy entity representation of the RepoFile."""
        return RepoFileEntity(
            id=self.id,
            repo_id=self.repo_id,
            sha256=self.sha256,
            path_json=self.path_json,
            stat_json=self.stat_json,
            mime_type=self.mime_type,
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            content=self.content,
            repo_path=self.repo_path,
            lines_json=self.lines_json,
        )

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().model_dump(),
            "repo_path": self.repo_path,
            "repo_id": self.repo_id,
        }

    @classmethod
    def populate(cls, file_path: Path, repo_id: str, repo_root: Path) -> "RepoFile":
        """
        Populate a RepoFile model from a file path.
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path).resolve()
            instance = super().populate(file_path)
            instance.type = "repo-file"
            instance.repo_id = repo_id
            instance.repo_path = str(file_path.relative_to(repo_root))
            return instance
        except Exception as e:
            raise RuntimeError(
                f"Error populating RepoFile model from path {file_path}: {e}"
            ) from e

    @field_validator("repo_path", mode="before")
    def validate_repo_path(cls, v: Any) -> Optional[str]:
        """
        Validator for 'repo_path' field to ensure it is a string or None.
        """
        if v is None:
            raise ValueError("repo_path cannot be None")
        if isinstance(v, Path):
            return v.as_posix()
        if not isinstance(v, str):
            raise ValueError("repo_path must be a string or Path")
        return v

    @field_validator("repo_id", mode="before")
    def validate_repo_id(cls, v: Any) -> Optional[str]:
        """
        Validator for 'repo_id' field to ensure it is a string or None.
        """
        if v is None:
            raise ValueError("repo_id cannot be None")
        if not isinstance(v, str):
            raise ValueError("repo_id must be a string")
        return v


class Repo(BaseDirectory):
    """
    Model representing a repository directory.

    Attributes:
        path_json (FilePath): The path model of the repository directory.
        stat_json (BaseFileStat): The file statistics model.
        tags (Optional[list[str]]): A list of tags associated with the repository.
        short_description (Optional[str]): A short description of the repository.
        long_description (Optional[str]): A long description of the repository.
        frozen (bool): Indicates if the repository is frozen (immutable).
        type (Literal["local", "cloned"]): The type of the repository directory.
        url (Optional[str]): The URL of the repository.
        files (List[RepoFileModel]): List of files in the repository directory.
        git_metadata (Optional[GitMetadata]): Git metadata associated with the repository.
        last_seen (Optional[datetime]): Timestamp when the repository was last seen.
    """

    repo_type: Literal["git-local", "git-cloned"] = Field(
        "git-local", description="The type of the repository directory"
    )
    url: Optional[str] = Field(None, description="The URL of the repository")
    files: List[RepoFile] = Field(
        default=[], description="List of files in the repository directory"
    )
    git_metadata: Optional[GitMetadata] = Field(
        None, description="Git metadata associated with the repository"
    )
    last_seen: Optional[datetime] = Field(
        None, description="Timestamp when the repository was last seen"
    )

    def _should_skip_file(self, file_rel_path: str) -> bool:
        """
        Determine if a file should be skipped based on its relative path.
        """
        return not (
            is_image_file(file_rel_path)
            or is_video_file(file_rel_path)
            or is_binary_file(file_rel_path)
        )

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "repo_type": self.repo_type,
            "url": self.url,
            "files": [file.model_dump() for file in self.files],
            "git_metadata": (
                self.git_metadata.model_dump() if self.git_metadata else None
            ),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }

    @field_validator("files", mode="before")
    def validate_files(cls, v):
        """
        Validator for 'files' field to ensure it is a list of RepoFileModel instances.
        """
        if not isinstance(v, list):
            raise ValueError("files must be a list")
        for item in v:
            if not isinstance(item, RepoFile):
                raise ValueError(
                    "Each item in files must be an instance of RepoFileModel"
                )
        return v

    @field_validator("git_metadata", mode="before")
    def validate_git_metadata(
        cls, v: Union[GitMetadata, dict[str, Any], None]
    ) -> Optional[GitMetadata]:
        """
        Validator for 'git_metadata' field to ensure it is a GitMetadata instance.
        """
        if isinstance(v, dict):
            return GitMetadata.model_validate(v)
        return v

    @field_validator("repo_type", mode="before")
    def validate_type(cls, v: Union[str, None]) -> Optional[str]:
        """
        Validator for 'repo_type' field to ensure it is either 'local' or 'cloned'.
        """
        if v not in {"git-local", "git-cloned"}:
            raise ValueError(f"Invalid repo type: {v}")
        return v

    @field_validator("url", mode="before")
    def validate_url(cls, v: Union[str, None]) -> Optional[str]:
        """
        Validator for 'url' field to ensure it is a valid URL or None.
        """
        if v is not None and not isinstance(v, str):
            raise ValueError("URL must be a string or None")
        if v is not None and not v.startswith(("http://", "https://", "git@")):
            raise ValueError("URL must start with 'http://', 'https://', or 'git@'")
        return v

    @field_validator("files", mode="before")
    def validate_files_type(
        cls, v: Union[List[RepoFile], List[dict[str, Any]]]
    ) -> List[RepoFile]:
        """
        Validator for 'files' field to ensure it is a list of RepoFile instances.
        """
        if all(isinstance(item, dict) for item in v):
            return [RepoFile.model_validate(item) for item in v]
        return v

    @classmethod
    def populate(
        cls,
        dir_path: Path,
        repo_type: Optional[Literal["git-cloned", "git-local"]] = "git-local",
    ) -> "Repo":
        """
        Populate a Repo model from a directory path.
        """
        try:
            if isinstance(dir_path, str):
                dir_path = Path(dir_path).resolve()
            instance = super().populate(dir_path)
            instance.git_metadata = get_git_metadata(dir_path)
            instance.url = (
                instance.git_metadata.remotes.get("origin")
                if instance.git_metadata
                else None
            )
            instance.repo_type = repo_type
            file_ls = git.Repo(dir_path).git.ls_files().splitlines()
            for file_rel_path in file_ls:
                file_abs_path = dir_path / file_rel_path
                if file_abs_path.is_file():
                    repo_file = RepoFile.populate(
                        file_abs_path, repo_id=instance.id, repo_root=dir_path
                    )
                    if repo_file._should_skip_file(file_rel_path):
                        continue
                    instance.files.append(repo_file)

            return instance
        except Exception as e:
            raise RuntimeError(
                f"Error populating Repo model from path {dir_path}: {e}"
            ) from e

    @property
    def docs(self) -> list[RepoFile]:
        """Return all documentation files in the repository."""
        return [file for file in self.files if file.suffix in {".md", ".rst", ".txt"}]

    @property
    def commits(self) -> List[GitCommit]:
        """
        Return the commit history from git_metadata.
        """
        if self.git_metadata and self.git_metadata.commit_history:
            return self.git_metadata.commit_history
        return []

    @property
    def repo_root(self) -> Path:
        """
        Return the root path of the repository based on its type.
        """
        if self.repo_type == "local":
            return self.Path
        elif self.repo_type == "cloned":
            return REMOTES_DIR / self.name

    @property
    def exists(self) -> bool:
        """
        Check if the repository root path exists in the filesystem.
        """
        return self.repo_root.exists()

    @property
    def entity(self) -> RepoEntity:
        """Return the SQLAlchemy entity representation of the repository."""
        return RepoEntity(
            id=self.id,
            stat_json=self.stat_json.model_dump(),
            path_json=self.path_json.model_dump(),
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            type=self.repo_type,
            url=self.url,
            git_metadata=(
                self.git_metadata.model_dump() if self.git_metadata else None
            ),
            last_seen=self.last_seen,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @property
    def file_entities(self) -> List[RepoFileEntity]:
        """Return the list of SQLAlchemy entity representations of the repository files."""
        return [file.entity for file in self.files]

    model_config = ConfigDict(
        from_attributes=True,
    )


class RepoScanResult(BaseScanResult):
    """
    Model representing the result of a local Git repository scan.

    Attributes:
        root: str: The root directory that was scanned.
        mode: Literal["git-local", "git-cloned"]: The scanning mode used.
        started_at: Optional[datetime]: Timestamp when the scan started.
        ended_at: Optional[datetime]: Timestamp when the scan ended.
        type (Literal["git-local"]): The type of scan, fixed to "git-local".
        repo_model (Optional[Repo]): The repository model containing details about the scanned repository.
    """

    type: Literal["git-local", "git-cloned"] = "git-local"
    repo_model: Optional[Repo] = Field(
        None,
        description="The repository model containing details about the scanned repository",
    )

    @field_validator("repo_model", mode="before")
    def validate_model(cls, v: Union[Repo, dict[str, Any]]) -> Repo:
        if isinstance(v, dict):
            return Repo.model_validate(v)
        return v

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "git_metadata": (
                self.git_metadata.model_dump() if self.git_metadata else None
            ),
            "repo_model": self.model.model_dump(),
        }


# endregion

__all__ = [
    "RepoEntity",
    "RepoFileEntity",
    "RepoFileLineEntity",
    "Repo",
    "RepoFile",
    "RepoScanResult",
    "GitMetadata",
    "GitCommit",
]
