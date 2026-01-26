# region Docstring
"""
core.models.file_system.audio_file
Persistence and domain models for indexing and working with audio files.
Overview:
- Provides SQLAlchemy entity to persist audio file metadata, transcripts, and duration.
- Provides Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.
Contents:
- SQLAlchemy entities:
    - AudioFileEntity:
        Persists a single audio file with path/stat metadata, SHA256 hash, optional
        transcript, and duration. Several columns are computed from JSON fields
        (e.g., filename, extension, size). Includes helper properties for model
        conversion, path/stat accessors, summary generation, and freeze/unfreeze
        functionality.
- Pydantic models:
    - AudioFile:
        A domain model representing a single audio file. Includes audio-specific
        attributes (duration, transcript_json, video_id for extracted audio),
        common file metadata (path/stat/tags/descriptions), and serialization
        helpers. Extends BaseFileModel with audio type discriminator.
Design notes:
- .model property on SQLAlchemy entity provides immediate conversion to Pydantic
    model for safe I/O layers.
- Computed columns reduce duplication and ensure consistent derivation of metadata
    from JSON fields without requiring application-side recomputation.
- Audio-specific fields (duration, transcript_json) support audio processing
    workflows and speech-to-text integrations.
- video_id field supports linking audio tracks extracted from video files.
"""
# endregion
# region Imports
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from core.database import Base
from core.models.file_system.base import BaseFileModel, BaseFileStat, FilePath
from pydantic import model_serializer
from sqlalchemy import Computed, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


# endregion
# region Sqlalchemy Model
class AudioFileEntity(Base):
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
        transcript (str): The actual transcript of the audio file.
        duration (float): Duration of the audio file in seconds.
    """

    __tablename__ = "audio_files"

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

    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stat_json: Mapped[dict] = mapped_column(String, nullable=False)
    path_json: Mapped[dict] = mapped_column(String, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frozen: Mapped[bool] = mapped_column(String, default=False, server_default="0")

    # Audio file specific column
    transcript: Mapped[str] = mapped_column(Text)
    duration: Mapped[float] = mapped_column(Integer, nullable=True)

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @property
    def model(self) -> "AudioFile":
        """Return the Pydantic model representation of the audio file."""
        return AudioFile.model_validate(
            {
                "type": "audio",
                "id": self.id,
                "path_json": self.path_json,
                "stat_json": self.stat_json,
                "mime_type": self.mime_type,
                "tags": self.tags,
                "short_description": self.short_description,
                "long_description": self.long_description,
                "frozen": self.frozen,
                "duration": self.duration,
                "transcript": self.transcript,
            }
        )

    @property
    def dict(self) -> dict[str, Optional[str]]:
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
            "duration": self.duration,
            "transcript": self.transcript,
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
# region Pydantic Model
class AudioFile(BaseFileModel):
    """
    A Pydantic model to represent an audio file.

    Attributes:
        id (Optional[int]): The unique identifier for the audio file.
        type (Literal["audio"]): The discriminator for audio file type.
        sha256 (str): The SHA256 hash of the file.
        path_json (PathModel): The path model of the directory.
        stat_json (BaseFileStatModel): The file statistics model of the directory.
        tags (Optional[list[str]]): A list of tags associated with the directory.
        short_description (Optional[str]): A short description of the directory.
        long_description (Optional[str]): A long description of the directory.
        frozen (bool): Indicates if the directory is frozen (immutable).
        type (Literal["audio"]): The discriminator for audio file type.
        duration (Optional[float]): Duration of the audio file in seconds.
        transcript (Optional[str]): Transcript of the audio content.
    """

    type: Literal["audio"] = "audio"
    duration: Optional[float] = None
    transcript_json: Optional[dict[str, Any]] = None
    video_id: Optional[int] = None  # If the audio is extracted from a video file

    def populate(self, file_path: Path) -> None:
        super().populate(file_path)
        self.duration = None
        self.transcript = None
        self.video_id = None

        # TODO: Populate duration using audio processing libraries like pydub or librosa.

    @model_serializer("json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "duration": self.duration,
            "transcript": self.transcript,
        }

    @property
    def entity(self) -> AudioFileEntity:
        return AudioFileEntity(
            id=self.id if self.id is not None else None,
            sha256=self.sha256,
            path_json=self.path_json.model_dump(),
            stat_json=self.stat_json.model_dump(),
            mime_type=self.mime_type,
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            duration=self.duration,
            transcript=self.transcript,
        )


# endregion

__all__ = ["AudioFileEntity", "AudioFile"]
