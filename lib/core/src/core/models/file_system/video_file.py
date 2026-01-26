# region Docstring
"""
core.models.file_system.video_file

Persistence and domain models for indexing and working with video files.

Overview:
- Provides a SQLAlchemy entity to persist video file metadata including path, stat info,
    content hash, and video-specific attributes (duration, resolution, codec).
- Provides Pydantic models mirroring the persisted entities for safe I/O, validation,
    and serialization.
- Includes scan result models for representing the output of video file discovery operations.

Contents:
- SQLAlchemy entities:
    - VideoFile_Table:
        Persists a single video file with path/stat metadata, content hash (SHA-256),
        and video-specific attributes (duration, width, height, resolution, codec).
        Computed columns derive filename, extension, and size from JSON fields.
        Includes helpers for equality (by sha256), hashing, and conversion to
        Pydantic models via .stat_model, .path_model, and .Path properties.
        Provides .summary for quick dictionary representation and .freeze/.unfreeze
        methods for immutability control.

- Pydantic models:
    - VideoFile:
        A domain model representing a single video file. Extends BaseFileModel with
        video-specific fields: duration, resolution (width, height tuple), codec.
        Includes a .populate() method to extract metadata from a video file using
        OpenCV (cv2) when available.
    - VideoScanResultModel:
        Represents the result of scanning a directory in mode="video". Carries the
        list of discovered video file paths. Includes validators for flexible input
        shapes and serialization helpers.

- TODO Models (planned):
    - VideoFrame: Represents a single frame extracted from a video with metadata.
    - VideoClip: Represents a segment/clip within a video with start/end times.
    - VideoProxyFile: Represents a lower-resolution proxy file for a video.
    - PreviewGIF: Represents a preview GIF generated from a video.

Design notes:
- Computed columns reduce duplication and ensure consistent derivation of metadata from
    JSON fields without requiring application-side recomputation.
- Pydantic validators normalize flexible input shapes (lists of dicts vs. strings).
- The .populate() method gracefully handles missing cv2 dependency for minimal environments.
- Equality and hashing are based on SHA-256 content hash for deduplication support.
"""

import subprocess

# endregion
# region Imports
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, field_validator, model_serializer
from sqlalchemy import (
    JSON,
    Boolean,
    Computed,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.base import (
    BaseFileModel,
    BaseFileStat,
    BaseScanResult,
    FilePath,
)
from core.database import Base


# endregion
# region Sqlalchemy Model
class VideoFileEntity(Base):
    """
    Model representing a video file in the file system.

    Attributes:
        id (int): Primary key.
        sha256 (str): SHA256 hash of the video file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the video file.
        tags (Optional[list[str]]): Tags associated with the video file.
        short_description (Optional[str]): Short description of the video file.
        long_description (Optional[str]): Long description of the video file.
        frozen (bool): Indicates if the file is frozen (immutable).
        duration (Optional[float]): Duration of the video in seconds.
        width (Optional[int]): Width of the video in pixels.
        height (Optional[int]): Height of the video in pixels.
        resolution (Optional[str]): Resolution of the video (e.g., '1920x1080').
        codec (Optional[str]): Codec used for the video (e.g., 'H.264').
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "video_files"

    id: Mapped[int] = mapped_column(primary_key=True)

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

    # Standard Columns
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    path_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    stat_json: Mapped[Dict[str, Any]] = mapped_column(JSON)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, default=None)
    short_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    long_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # Video Specific
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<VideoFile(id={self.id}, sha256='{self.sha256}')>"  # noqa: E501

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VideoFileEntity):
            return NotImplemented

        return self.sha256 == other.sha256

    def __hash__(self) -> int:
        return hash(self.sha256)

    @property
    def model(self) -> "VideoFile":
        """Return the Pydantic model representation of the video file."""
        return VideoFile.model_validate(
            {
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
                "width": self.width,
                "height": self.height,
                "resolution": (
                    tuple(map(int, self.resolution.split("x")))
                    if self.resolution
                    else None
                ),
                "codec": self.codec,
            }
        )

    @property
    def dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the VideoFile_Table."""
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
            "width": self.width,
            "height": self.height,
            "resolution": self.resolution,
            "codec": self.codec,
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
    def summary(self) -> dict:
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
# region Pydantic Model for Video File
class VideoFile(BaseFileModel):
    """
    A Pydantic model to represent a video file with its metadata.

    Attributes:
        type (Literal["video"]): The discriminator for video file type.
        sha256 (str): The SHA256 hash of the file.
        stat_json (BaseFileStatModel): The file statistics model.
        path_json (PathModel): The path model of the file.
        mime_type (Optional[str]): The MIME type of the file.
        tags (Optional[list[str]]): A list of tags associated with the file.
        short_description (Optional[str]): A short description of the file.
        long_description (Optional[str]): A long description of the file.
        frozen (bool): Indicates if the file is frozen (immutable).
        duration (Optional[float]): Duration of the video in seconds.
        resolution (Optional[tuple[int, int]]): Resolution of the video as (width, height).
        height (Optional[int]): Height of the video in pixels.
        width (Optional[int]): Width of the video in pixels.
        codec (Optional[str]): Codec used for the video.
    """

    type: Literal["video"] = "video"
    duration: Optional[float] = None
    resolution: Optional[tuple[int, int]] = None
    height: Optional[int] = None
    width: Optional[int] = None
    codec: Optional[str] = None
    # frames: Optional
    # preview_gif_b64_data: Optional[str] = None  # TODO: Implement preview generation
    # timestamped_frames: Optional[dict[float, str]] = None  # TODO: Implement frame extraction

    def _get_video_duration(self, file_path: Path) -> float:
        """Helper method to get video duration using ffmpeg."""
        import subprocess

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return float(result.stdout)

    def _get_video_codec(self, file_path: Path) -> str:
        """Helper method to get video codec using ffmpeg."""

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return result.stdout.decode().strip()

    def _get_video_resolution(self, file_path: Path) -> tuple[int, int]:
        """Helper method to get video resolution using ffmpeg."""
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=s=x:p=0",
                str(file_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        resolution_str = result.stdout.decode().strip()
        width, height = map(int, resolution_str.split("x"))
        return width, height

    @classmethod
    def populate(cls, file_path: Path) -> "VideoFile":
        """Populate video-specific metadata using ffmpeg."""
        instance = super().populate(file_path)
        try:
            duration = instance._get_video_duration(file_path)
            codec = instance._get_video_codec(file_path)
            width, height = instance._get_video_resolution(file_path)
            if width and height:
                resolution = (width, height)
        except Exception as e:
            # Handle exceptions (e.g., ffprobe not found, invalid file)
            raise Exception(f"Error populating video metadata: {e}")
        instance.duration = duration
        instance.codec = codec
        instance.width = width
        instance.height = height
        if width and height:
            instance.resolution = resolution
        return instance

    @property
    def entity(self) -> VideoFileEntity:
        return VideoFileEntity(
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
            width=self.width,
            height=self.height,
            resolution=(
                f"{self.width}x{self.height}" if self.width and self.height else None
            ),
            codec=self.codec,
        )


class VideoScanResult(BaseScanResult):
    """
    Model representing the result of a video scan.

    Attributes:
        root (str): The root directory that was scanned.
        mode (Literal["video"]): The scanning mode used.
        started_at (Optional[datetime]): Timestamp when the scan started.
        ended_at (Optional[datetime]): Timestamp when the scan ended.
        files (List[str]): List of video file paths found during the scan.
    """

    type: Literal["video"] = "video"
    files: List[str] = Field(
        default_factory=list,
        description="List of video file paths found during the scan",
    )

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "files": self.files,
        }

    @field_validator("files", mode="before")
    def validate_files(cls, v: Union[List[str], List[dict[str, Any]]]) -> List[str]:
        if all(isinstance(item, dict) for item in v):
            return [item["path"] for item in v if "path" in item]
        return v


# endregion

# region TODO Models
# TODO:
# class VideoFrame(Basemodel):
#    video_id: int = Field(..., description="Reference to the video file model")
#    frame_number: int = Field(..., description="The frame number in the video")
#    frame_timestamp: datetime = Field(default_factory=settings.get_current_time())
#    img_data_b64: Optional[str] = Field(None, description="Base64 encoded preview image data")
#    action_tags: Optional[List[str]] = Field(None, description="List of action tags associated with the frame")
#
# class VideoClip(Basemodel):
#    video_id: int = Field(..., description="Reference to the video file model")
#    preview_gif_b64_data: Optional[str] = Field(None, description="Base64 encoded preview GIF data for the clip")
#    title: Optional[str] = Field(None, description="Optional title for the video clip")
#    annotation: Optional[str] = Field(None, description="Optional annotation for the video clip")
#    start_time: float = Field(default=0.0, description="Start time of the clip in seconds")
#    end_time: float = Field(default=0.0, description="End time of the clip in seconds")
#
# class VideoProxyFile(Basemodel):
#    video_id: int = Field(..., description="Reference to the video file model")
#    proxy_file_path: str = Field(..., description="Path to the proxy video file")
#    resolution: Optional[tuple[int, int]] = Field(None, description="Resolution of the proxy video")
#    bitrate: Optional[int] = Field(None, description="Bitrate of the proxy video in kbps")
#    codec: Optional[str] = Field(None, description="Codec used for the proxy video")
#
# class PreviewGIF(BaseModel):
#     video_id: int = Field(..., description="Reference to the video file model")
#     gif_b64_data: Optional[str] = Field(None, description="Base64 encoded preview GIF data for the video")
# endregion

__all__ = ["VideoFileEntity", "VideoFile", "VideoScanResult"]
