# region Docstring
"""
core.models.file_system.image_file

Persistence and domain models for indexing and working with image files.

Overview:
- Provides SQLAlchemy entities to persist image files with metadata, thumbnails, and EXIF data.
- Provides Pydantic models mirroring the persisted entities for safe I/O, validation,
    and serialization.
- Extends base file system models from core.models.file_system.base for consistent
    path/stat handling and file metadata representation.

Contents:
- SQLAlchemy entities:
    - ImageFileEntity:
        Persists an image file with path/stat metadata (as JSON), SHA256 hash, base64 encoded
        image data, thumbnail data, and EXIF metadata. Several columns are computed from JSON
        fields (e.g., filename, extension, size_bytes, modified_at_fs). Includes a .model
        property to convert to the ImageFile Pydantic model and convenience properties for
        accessing stat/path models (.stat_model, .path_model, .Path). Provides .summary for
        quick metadata access and .freeze()/.unfreeze() methods for immutability toggling.

- Pydantic models:
    - ImageFile:
        A domain model extending BaseFileModel representing an image file. Includes base64
        encoded data for both the full image (b64_data) and thumbnail (thumbnail_b64_data),
        EXIF metadata (exif_data), format information (fmt), and NSFW flag (is_nsfw).
        The populate() method handles reading image files, extracting EXIF data, generating
        thumbnails, and encoding to base64. Provides helper properties for generating
        HTML/Markdown image tags (html_thumbnail_tag, md_thumbnail_tag, html_img_tag,
        md_img_tag) and an .entity property for SQLAlchemy conversion.

- Scan Result models:
    - ImageScanResult:
        Extends BaseScanResult representing the result of scanning a directory in mode="image".
        Carries the list of discovered ImageFile objects (files). Includes validators for
        type consistency and serialization helpers.

Design notes:
- All models use Pydantic v2 conventions with field_validator, field_serializer,
    and model_serializer decorators.
- .model properties on SQLAlchemy entities provide an immediate conversion to Pydantic
    models for safe I/O layers.
- The ImageFile.populate() method handles reading image files, extracting EXIF data,
    generating thumbnails (default 512x512), and encoding to base64.
- Computed columns in ImageFileEntity reduce duplication and ensure consistent derivation
    of metadata from JSON fields without requiring application-side recomputation.
- Thumbnail generation maintains aspect ratio and handles transparency for images with
    alpha channels (RGBA, LA, or P mode with transparency).
- EXIF data extraction handles various byte encodings (UTF-8, unicode_escape, latin-1)
    with graceful fallback.
- Tag validation (inherited from BaseFileModel) ensures lowercase, dash-separated,
    hash-prefixed format for consistency.
"""
# endregion
# region Imports
import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from PIL import ExifTags, Image
from pydantic import Field, field_validator, model_serializer
from sqlalchemy import JSON, Boolean, Computed, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.models.file_system.base import (
    BaseFileModel,
    BaseFileStat,
    BaseScanResult,
    FilePath,
)


# endregion
# region Sqlalchemy Model
class ImageFileEntity(Base):
    """
    Model representing an image file in the file system.

    Attributes:
        id (str): Primary key.
        sha256 (str): SHA256 hash of the image file.
        path_json (Dict[str, Any]): JSON representation of the file path.
        stat_json (Dict[str, Any]): JSON representation of the file's stat information.
        mime_type (Optional[str]): MIME type of the image file.
        tags (Optional[list[str]]): Tags associated with the image file.
        short_description (Optional[str]): Short description of the image file.
        long_description (Optional[str]): Long description of the image file.
        frozen (bool): Indicates if the file is frozen (immutable).
        fmt (Optional[str]): Format of the image (e.g., 'JPEG', 'PNG').
        b64_data (str): Base64 encoded image data.
        thumbnail_b64_data (Optional[str]): Base64 encoded thumbnail image data.
        exif_data (Dict[str, Any]): EXIF metadata of the image.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "image_files"

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
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, default=None)
    short_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    long_description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    frozen: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # Image Specific
    fmt: Mapped[Optional[str]] = mapped_column(String(10))
    b64_data: Mapped[str] = mapped_column(Text)
    thumbnail_b64_data: Mapped[Optional[str]] = mapped_column(Text)
    exif_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_nsfw: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ImageFile(id={self.id}, sha256='{self.sha256}')>"  # noqa: E501

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageFileEntity):
            return NotImplemented

        return self.sha256 == other.sha256

    def __hash__(self) -> int:
        return hash(self.sha256)

    @property
    def model(self) -> "ImageFile":
        """Return the Pydantic model representation of the image file."""
        return ImageFile.model_validate(
            {
                "type": "image",
                "id": self.id,
                "path_json": self.path_json,
                "stat_json": self.stat_json,
                "mime_type": self.mime_type,
                "tags": self.tags,
                "short_description": self.short_description,
                "long_description": self.long_description,
                "frozen": self.frozen,
                "fmt": self.fmt,
                "b64_data": self.b64_data,
                "thumbnail_b64_data": self.thumbnail_b64_data,
                "exif_data": self.exif_data,
                "is_nsfw": self.is_nsfw,
            }
        )

    @property
    def dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the ImageFileEntity."""
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
            "fmt": self.fmt,
            "b64_data": self.b64_data,
            "thumbnail_b64_data": self.thumbnail_b64_data,
            "exif_data": self.exif_data,
            "is_nsfw": self.is_nsfw,
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
class ImageFile(BaseFileModel):
    """
    A Pydantic model to represent an image file with its dimensions.

    Attributes:
        type (Literal["image"]): The discriminator for image file type.
        sha256 (str): The SHA256 hash of the file.
        stat_json (BaseFileStatModel): The file statistics model.
        path_json (PathModel): The path model of the file.
        mime_type (Optional[str]): The MIME type of the file.
        tags (Optional[list[str]]): A list of tags associated with the file.
        short_description (Optional[str]): A short description of the file.
        long_description (Optional[str]): A long description of the file.
        frozen (bool): Indicates if the file is frozen (immutable).
        b64_data (Optional[str]): Base64 encoded string of the full image.
        thumbnail_b64_data (Optional[str]): Base64 encoded string of the thumbnail image.
        exif_data (dict[str, Any]): EXIF metadata extracted from the image.
        fmt (Optional[str]): The image format (e.g., 'jpeg', 'png').
        is_nsfw (Optional[bool]): Flag indicating if the image is NSFW. DEFAULT: False
    """

    type: Literal["image"] = "image"
    b64_data: Optional[str] = Field(
        None, description="Base64 encoded string of the full image"
    )
    thumbnail_b64_data: Optional[str] = Field(
        None, description="Base64 encoded string of the thumbnail image"
    )
    exif_data: dict[str, Any] = Field(
        {}, description="EXIF metadata extracted from the image"
    )
    fmt: Optional[str] = Field(
        None, description="The image format (e.g., 'jpeg', 'png')"
    )
    is_nsfw: Optional[bool] = Field(
        False, description="Flag indicating if the image is NSFW. DEFAULT: False"
    )

    @classmethod
    def populate(cls, file_path: Path, thumbnail_size: tuple = (512, 512)) -> None:
        """
        Populate the model attributes based on the given image file path.

        Args:
            file_path (Path): The path to the image file.
            thumbnail_size (tuple): Size of the thumbnail to generate. DEFAULT: (512, 512)

        Returns:
            None
        """
        super().populate(file_path)

        try:
            img = Image.open(file_path)
            cls.fmt = img.format.lower() if img.format else "unknown"

            # Encode full image to base64
            buffered = BytesIO()
            img.save(buffered, format=img.format)
            cls.b64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # copy the image for modifications
            img_copy = img.copy()

            # shrink the copy to fit longest side to thumbnail_size while maintaining aspect ratio
            img_copy.thumbnail(thumbnail_size)

            # fill the background with transparency if image has alpha channel
            if img_copy.mode in ("RGBA", "LA") or (
                img_copy.mode == "P" and "transparency" in img_copy.info
            ):
                background = Image.new("RGBA", img_copy.size, (255, 255, 255, 0))
                background.paste(
                    img_copy, mask=img_copy.split()[3]
                )  # 3 is the alpha channel
                img_copy = background
            else:
                img_copy = img_copy.convert("RGB")
            # Encode thumbnail to base64
            thumb_buffered = BytesIO()
            img_copy.save(thumb_buffered, format=img.format)
            cls.thumbnail_b64_data = base64.b64encode(thumb_buffered.getvalue()).decode(
                "utf-8"
            )
            try:
                exif = img.getexif()
                if exif:
                    cls.exif_data = {
                        ExifTags.TAGS.get(tag, tag): value
                        for tag, value in exif.items()
                    }
                    # Some exif values are bytes, decode them if possible
                    for key, value in cls.exif_data.items():
                        if isinstance(value, bytes):
                            try:
                                cls.exif_data[key] = value.decode(
                                    "utf-8", errors="ignore"
                                )
                            except Exception:
                                try:
                                    # I know some of them use unicode encoding
                                    cls.exif_data[key] = value.decode(
                                        "unicode_escape", errors="ignore"
                                    )
                                except Exception:
                                    # try latin-1 as last resort
                                    try:
                                        cls.exif_data[key] = value.decode(
                                            "latin-1", errors="ignore"
                                        )
                                    except Exception:
                                        continue
            except Exception as e:
                print(f"Error processing image file {file_path}: {e}")

        except Exception as e:
            print(f"Error extracting EXIF data from image file {file_path}: {e}")
        return cls

    @property
    def html_thumbnail_tag(self) -> Optional[str]:
        """
        Generate an HTML img tag for the thumbnail image.

        Returns:
            Optional[str]: HTML img tag string if thumbnail data is available, else None.
        """
        if self.thumbnail_b64_data and self.fmt:
            return f'<img src="data:image/{self.fmt};base64,{self.thumbnail_b64_data}" alt="Thumbnail"/>'
        return None

    @property
    def md_thumbnail_tag(self) -> Optional[str]:
        """
        Generate a Markdown image tag for the thumbnail image.

        Returns:
            Optional[str]: Markdown image tag string if thumbnail data is available, else None.
        """
        if self.thumbnail_b64_data and self.fmt:
            return (
                f"![Thumbnail](data:image/{self.fmt};base64,{self.thumbnail_b64_data})"
            )
        return None

    @property
    def html_img_tag(self) -> Optional[str]:
        """
        Generate an HTML img tag for the full image.

        Returns:
            Optional[str]: HTML img tag string if image data is available, else None.
        """
        if self.b64_data and self.fmt:
            return (
                f'<img src="data:image/{self.fmt};base64,{self.b64_data}" alt="Image"/>'
            )
        return None

    @property
    def md_img_tag(self) -> Optional[str]:
        """
        Generate a Markdown image tag for the full image.

        Returns:
            Optional[str]: Markdown image tag string if image data is available, else None.
        """
        if self.b64_data and self.fmt:
            return f"![Image](data:image/{self.fmt};base64,{self.b64_data})"
        return None

    @property
    def entity(self) -> ImageFileEntity:
        return ImageFileEntity(
            id=self.id,
            sha256=self.sha256,
            path_json=self.path_json,
            stat_json=self.stat_json,
            mime_type=self.mime_type,
            tags=self.tags,
            short_description=self.short_description,
            long_description=self.long_description,
            frozen=self.frozen,
            fmt=self.fmt,
            b64_data=self.b64_data if self.b64_data is not None else "",
            thumbnail_b64_data=self.thumbnail_b64_data,
            exif_data=self.exif_data,
            is_nsfw=self.is_nsfw if self.is_nsfw is not None else False,
        )


# endregion
# region Scan Result Model
class ImageScanResult(BaseScanResult):
    """
    Model representing the result of an image scan.

    Attributes:
        root (str): The root directory that was scanned.
        mode (Literal["image"]): The scanning
        started_at (Optional[datetime]): Timestamp when the scan started.
        ended_at (Optional[datetime]): Timestamp when the scan ended.
        files (List[ImageFileModel]): List of image files found during the scan.
    """

    mode: Literal["image"] = "image"
    files: List[ImageFile] = Field(
        default_factory=list, description="List of image files found during the scan"
    )

    @field_validator("files", mode="before")
    def validate_files(
        cls, v: Union[List[ImageFile], List[dict[str, Any]]]
    ) -> List[ImageFile]:
        if all(isinstance(item, dict) for item in v):
            return [ImageFile.model_validate(item) for item in v]
        return v

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "files": [file.model_dump() for file in self.files],
        }


# endregion

__all__ = ["ImageFileEntity", "ImageFile", "ImageScanResult"]
