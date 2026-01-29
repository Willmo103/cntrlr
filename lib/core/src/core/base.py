# region Docstring
"""
core.models.file_system.base
Base persistence and domain models for file system entities and scan operations.
Overview:
- Provides foundational Pydantic models for representing file paths, file statistics,
    and file metadata across different operating systems.
- Defines base classes for files, directories, text files, and scan results that can
    be extended by domain-specific implementations (e.g., Obsidian, Git, media files).
- Includes platform-specific file stat models for macOS, Linux, and Windows.
Contents:
- Path Models:
    - FilePath:
        A Pydantic model representing pathlib.Path attributes with full decomposition
        into name, suffix, stem, parent, parts, etc. Includes a .Path property to
        reconstruct the original Path object.
- File Statistics Models:
    - BaseFileStat:
        Base model for POSIX file statistics (st_mode, st_size, st_atime, st_mtime,
        st_ctime, etc.). Includes serialization that converts timestamps to ISO 8601
        datetime strings.
    - MacOSFileStat:
        Extends BaseFileStat with macOS/BSD-specific fields (st_flags, st_gen,
        st_birthtime).
    - LinuxFileStat:
        Extends BaseFileStat with Linux-specific fields (st_atim, st_mtim, st_ctim,
        and nanosecond variants).
    - WindowsFileStat:
        Extends BaseFileStat with Windows-specific fields (st_file_attributes,
        st_reparse_tag).
- File Models:
    - BaseFileModel:
        Abstract base for all file representations. Includes SHA256 hash, path/stat JSON,
        MIME type, tags, descriptions, and frozen status. Provides computed id property
        (SHA256 of path + content hash), validators for path/stat/tags, and a populate()
        method to auto-fill attributes from a file path.
    - GenericFile:
        Simple file model with type="file" for unclassified files.
    - TextFileLine:
        Represents a single line in a text file with file_id, content, line_number,
        and content_hash. Includes is_empty and line_length properties.
    - BaseTextFile:
        Extends BaseFileModel for text files. Adds content (full text) and lines_json
        (list of TextFileLine). The populate() method reads file content and splits
        into enumerated lines.
- Directory Models:
    - BaseDirectory:
        Represents a directory with path/stat JSON, tags, descriptions, and frozen
        status. Provides a .Path property and is_empty() method.
- Scan Result Models:
    - BaseScanResult:
        Base model for scan operation results. Includes root path, scanning mode
        (git-local, git-cloned, image, video, database, obsidian, docs, pdf, all),
        started_at/ended_at timestamps, and duration_seconds property. Validators
        handle ISO string parsing for timestamps.
Design Notes:
- All models use Pydantic v2 conventions with field_validator, field_serializer,
    and model_serializer decorators.
- Timestamp fields are consistently serialized to ISO 8601 strings for API compatibility.
- The populate() pattern allows models to be instantiated empty and filled from
    actual file system data via utility functions.
- Tag validation ensures lowercase, dash-separated, hash-prefixed format for consistency.
- Platform-specific stat models allow accurate representation of file metadata across
    macOS, Linux, and Windows environments.
"""

# endregion
# region Imports
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from .utils import (
    get_file_sha256,
    get_file_stat_model,
    get_mime_type,
    get_path_model,
    is_markdown_formattable,
)

# endregion
# region Base File System Models
# --- FILE PART MODELS ---
# These were the very fisrt portion of this codebase that I wrote. I had been
# Looking for the best way to map all the file context that my adhd brain wants
# to store in order to make sense of files on disk.


# region Path Model
class FilePath(BaseModel):
    """
    A Pydantic model to represent pathlib.Path attributes.

    Attributes:
        name (str): The final path component.
        suffix (str): The file extension of the final path component.
        suffixes (list[str]): A list of all suffixes in the final path component.
        stem (str): The final path component without its suffix.
        parent (str): The parent directory of the path.
        parents (list[str]): A list of all parent directories.
        anchor (str): The part of the path before the directories.
        drive (str): The drive letter (Windows only).
        root (str): The root of the path.
        parts (list[str]): A tuple giving access to the path’s various components.
        is_absolute (bool): Whether the path is absolute.

    Properties:
        full_path (str): The reconstructed full path from its components.

    Example:
        >>> PathModel(
        ...     name='file.txt',
        ...     suffix='.txt',
        ...     suffixes=['.txt'],
        ...     stem='file',
        ...     parent='/home/user/docs',
        ...     parents=['/home/user', '/home', '/'],
        ...     anchor='/',
        ...     drive='',
        ...     root='/',
        ...     parts=['/', 'home', 'user', 'docs', 'file.txt'],
        ...     is_absolute=True
        ... )
        PathModel(
            name='file.txt',
            suffix='.txt',
            suffixes=['.txt'],
            stem='file',
            parent='/home/user/docs',
            parents=['/home/user', '/home', '/'],
            anchor='/',
            drive='',
            root='/',
            parts=['/', 'home', 'user', 'docs', 'file.txt'],
            is_absolute=True
        )
        >>> # Print the full path
        >>> print(model.full_path)
        /home/user/docs/file.txt
    """

    name: str = Field(..., description="The final path component")
    suffix: str = Field(
        ..., description="The file extension of the final path component"
    )
    suffixes: list[str] = Field(
        ..., description="A list of all suffixes in the final path component"
    )
    stem: str = Field(..., description="The final path component without its suffix")
    parent: str = Field(..., description="The parent directory of the path")
    parents: list[str] = Field(..., description="A list of all parent directories")
    anchor: str = Field(..., description="The part of the path before the directories")
    drive: str = Field(..., description="The drive letter (Windows only)")
    root: str = Field(..., description="The root of the path")
    parts: list[str] = Field(
        ..., description="A tuple giving access to the path’s various components"
    )
    is_absolute: bool = Field(..., description="Whether the path is absolute")

    def _path(self) -> Path:
        """
        Helper method to reconstruct the full Path object from its components.
        """
        return Path(*self.parts)

    @property
    def Path(self) -> Path:
        """
        Reconstruct the full path from its components.

        Returns:
            Path: the full Path object.

        Example:
            >>> model = PathModel(
            ...     name='file.txt',
            ...     suffix='.txt',
            ...     suffixes=['.txt'],
            ...     stem='file',
            ...     parent='/home/user/docs',
            ...     parents=['/home/user', '/home', '/'],
            ...     anchor='/',
            ...     drive='',
            ...     root='/',
            ...     parts=['/', 'home', 'user', 'docs', 'file.txt'],
            ...     is_absolute=True
            ... )
            >>> print(model.full_path.as_posix())
            /home/user/docs/file.txt
        """
        return self._path()

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "name": self.name,
            "suffix": self.suffix,
            "suffixes": self.suffixes,
            "stem": self.stem,
            "parent": self.parent,
            "parents": self.parents,
            "anchor": self.anchor,
            "drive": self.drive,
            "root": self.root,
            "parts": self.parts,
            "is_absolute": self.is_absolute,
        }

    @model_validator(mode="before")
    def validate_parts(cls, data):
        """
        Ensure that 'parts' and 'parents' are lists of strings.
        """
        if "parts" in data and not isinstance(data["parts"], list):
            raise ValueError("'parts' must be a list of strings.")
        if "parents" in data and not isinstance(data["parents"], list):
            raise ValueError("'parents' must be a list of strings.")
        return data


# endregion
# region File Stat Models
class BaseFileStat(BaseModel):
    """
    Base Pydantic model to represent file statistics.

    Attributes:
        st_mode (Optional[int]): Protection bits.
        st_ino (Optional[int]): Inode number.
        st_dev (Optional[int]): Device.
        st_nlink (Optional[int]): Number of hard links.
        st_uid (Optional[int]): User ID of owner.
        st_gid (Optional[int]): Group ID of owner.
        st_size (Optional[int]): Size of file, in bytes.
        st_atime (Optional[float]): Time of most recent access.
        st_mtime (Optional[float]): Time of most recent content modification.
        st_ctime (Optional[float]): Platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows.
        st_atime_ns (Optional[int]): Time of most recent access, in nanoseconds.
        st_mtime_ns (Optional[int]): Time of most recent content modification, in nanoseconds.
        st_ctime_ns (Optional[int]): Platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows, in nanoseconds.
        st_blocks (Optional[int]): Number of 512-byte blocks allocated.
        st_blksize (Optional[int]): File system block size.
        st_rdev (Optional[int]): Device type (if inode device).

    Methods:
        to_yaml() -> str: Serialize the model to a YAML string.
        from_yaml(yaml_str: str) -> BaseFileStatModel: Deserialize a YAML string to an instance of the model.

    Attributes:
        st_mode (Optional[int]): Protection bits.
        st_ino (Optional[int]): Inode number.
        st_dev (Optional[int]): Device.
        st_nlink (Optional[int]): Number of hard links.
        st_uid (Optional[int]): User ID of owner.
        st_gid (Optional[int]): Group ID of owner.
        st_size (Optional[int]): Size of file, in bytes.
        st_atime (Optional[float]): Time of most recent access.
        st_mtime (Optional[float]): Time of most recent content modification.
        st_ctime (Optional[float]): Platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows.
        st_atime_ns (Optional[int]): Time of most recent access, in nanoseconds.
        st_mtime_ns (Optional[int]): Time of most recent content modification, in nanoseconds.
        st_ctime_ns (Optional[int]): Platform dependent; time of most recent metadata change on Unix, or the time of creation on Windows, in nanoseconds.
        st_blocks (Optional[int]): Number of 512-byte blocks allocated.
        st_blksize (Optional[int]): File system block size.
        st_rdev (Optional[int]): Device type (if inode device).

    Example:
        >>> stat = BaseFileStatModel(
        ...     st_mode=33206,
        ...     st_ino=123456,
        ...     st_dev=2050,
        ...     st_nlink=1,
        ...     st_uid=1000,
        ...     st_gid=1000,
        ...     st_size=2048,
        ...     st_atime=1625077765.0,
        ...     st_mtime=1625077765.0,
        ...     st_ctime=1625077765.0,
        ...     st_atime_ns=1625077765000000000,
        ...     st_mtime_ns=1625077765000000000,
        ...     st_ctime_ns=1625077765000000000,
        ...     st_blocks=8,
        ...     st_blksize=4096,
        ...     st_rdev=0
        ... )
        >>> yaml_str = stat.to_yaml()
        >>> print(yaml_str)
        st_mode: 33206
        st_ino: 123456
        st_dev: 2050
        st_nlink: 1
        st_uid: 1000
        st_gid: 1000
        st_size: 2048
        st_atime: 1625077765.0
        st_mtime: 1625077765.0
        st_ctime: 1625077765.0
        st_atime_ns: 1625077765000000000
        st_mtime_ns: 1625077765000000000
        st_ctime_ns: 1625077765000000000
        st_blocks: 8
        st_blksize: 4096
        st_rdev: 0
        >>> # Deserialize from YAML
        >>> stat2 = BaseFileStatModel.from_yaml(yaml_str)
        >>> print(stat2)
        st_mode=33206 st_ino=123456 st_dev=2050 st_n st_nlink=1 st_uid=1000 st_gid=1000 st_size=2048 st_atime=1625077765.0 st_mtime=1625077765.0 st_ctime=1625077765.0 st_atime_ns=1625077765000000000 st_mtime_ns=1625077765000000000 st_ctime_ns=1625077765000000000 st_blocks=8 st_blksize=4096 st_rdev=0
    """

    st_mode: Optional[int] = None
    st_ino: Optional[int] = None
    st_dev: Optional[int] = None
    st_nlink: Optional[int] = None
    st_uid: Optional[int] = None
    st_gid: Optional[int] = None
    st_size: Optional[int] = None

    st_atime: Optional[float] = None
    st_mtime: Optional[float] = None
    st_ctime: Optional[float] = None

    st_atime_ns: Optional[int] = None
    st_mtime_ns: Optional[int] = None
    st_ctime_ns: Optional[int] = None

    st_blocks: Optional[int] = None
    st_blksize: Optional[int] = None
    st_rdev: Optional[int] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True, ignore_extra=True, check_fields=False
    )


class MacOSFileStat(BaseFileStat):
    """
    A Pydantic model to represent macOS/BSD specific file statistics.

    Attributes:
        st_flags (Optional[int]): File flags.
        st_gen (Optional[int]): File generation number.
        st_birthtime (Optional[float]): Time of file creation.


    Methods:
        to_yaml() -> str: Serialize the model to a YAML string.
        from_yaml(yaml_str: str) -> MacOSFileStatModel: Deserialize a YAML string to an instance of the model.

    Example:
        >>> mac_stat = MacOSFileStatModel(
        ...     ... BaseFileStatModel attributes ...,
        ...     st_flags=8388608,
        ...     st_gen=1,
        ...     st_birthtime=1625077765.0
        ... )
        >>> yaml_str = mac_stat.to_yaml()
        >>> print(yaml_str)
        st_mode: ...
    """

    # macOS/BSD-specific
    st_flags: Optional[int] = None
    st_gen: Optional[int] = None
    st_birthtime: Optional[float] = None

    @model_serializer()
    def convert_to_iso_datetimes(self) -> dict:
        """
        Convert timestamp fields to ISO 8601 datetime strings during serialization.
        """
        data = super().convert_to_iso_datetimes()
        if data.get("st_birthtime") is not None:
            data["st_birthtime"] = datetime.fromtimestamp(
                data["st_birthtime"], tz=datetime.now()
            ).isoformat()
        return data


class LinuxFileStat(BaseFileStat):
    """
    A Pydantic model to represent Linux-specific file statistics.

    Attributes:
        st_atim (Optional[float]): Time of most recent access.
        st_mtim (Optional[float]): Time of most recent content modification.
        st_ctim (Optional[float]): Time of most recent metadata change.
        st_ctimensec (Optional[int]): Time of most recent metadata change, in nanoseconds.
        st_mtimensec (Optional[int]): Time of most recent content modification, in nanoseconds.
        st_atimensec (Optional[int]): Time of most recent access, in nanoseconds.

    Methods:
        to_yaml() -> str: Serialize the model to a YAML string.
        from_yaml(yaml_str: str) -> LinuxFileStatModel: Deserialize a YAML string to an instance of the model.

    Example:
        >>> linux_stat = LinuxFileStatModel(
        ...     ... BaseFileStatModel attributes ...,
        ...     st_atim=1625077765.0,
        ...     st_mtim=1625077765.0,
        ...     st_ctim=1625077765.0,
        ...     st_ctimensec=0,
        ...     st_mtimensec=0,
        ...     st_atimensec=0
        ... )
        >>> yaml_str = linux_stat.to_yaml()
        >>> print(yaml_str)
        st_mode: ...
    """

    # Linux-specific
    st_atim: Optional[float] = None
    st_mtim: Optional[float] = None
    st_ctim: Optional[float] = None
    st_ctimensec: Optional[int] = None
    st_mtimensec: Optional[int] = None
    st_atimensec: Optional[int] = None

    @model_serializer()
    def convert_to_iso_datetimes(self) -> dict:
        """
        Convert timestamp fields to ISO 8601 datetime strings during serialization.
        """
        data = super().convert_to_iso_datetimes()
        for field in ["st_atim", "st_mtim", "st_ctim"]:
            if data.get(field) is not None:
                data[field] = datetime.fromtimestamp(
                    data[field], tz=datetime.now()
                ).isoformat()
        return data


class WindowsFileStat(BaseFileStat):
    """
    A Pydantic model to represent Windows-specific file statistics.

    Attributes:
        st_file_attributes (Optional[int]): File attributes.
        st_reparse_tag (Optional[int]): Reparse point tag.

    Methods:
        to_yaml() -> str: Serialize the model to a YAML string.
        from_yaml(yaml_str: str) -> WindowsFileStatModel: Deserialize a YAML string to an instance of the model.

    Example:
        >>> win_stat = WindowsFileStatModel(
        ...     ... BaseFileStatModel attributes ...,
        ...     st_file_attributes=32,
        ...     st_reparse_tag=0
        ... )
        >>> yaml_str = win_stat.to_yaml()
        >>> print(yaml_str)
        st_mode: ...
    """

    # Windows-specific
    st_file_attributes: Optional[int] = None
    st_reparse_tag: Optional[int] = None


# endregion
# endregion
# region Base File Models


class BaseFileModel(BaseModel):
    """
    A Pydantic model to represent a file with its path, SHA256 hash, and file statistics.
    Attributes:
        type (str): The discriminator for file type (e.g., 'file', 'text', 'image').
        sha256 (str): The SHA256 hash of the file.
        stat_json (BaseFileStatModel): The file statistics model.
        path_json (PathModel): The path model of the file.
        mime_type (Optional[str]): The MIME type of the file.
        tags (Optional[list[str]]): A list of tags associated with the file.
        short_description (Optional[str]): A short description of the file.
        long_description (Optional[str]): A long description of the file.
        frozen (bool): Indicates if the file is frozen (immutable).
    """

    type: Literal["file", "text", "image", "video", "json", "sqlite"] = "file"
    sha256: str = Field(..., description="SHA256 hash of the file")
    stat_json: BaseFileStat = Field(..., description="File statistics model")
    path_json: FilePath = Field(..., description="Path model of the file")
    mime_type: str = Field(..., description="MIME type of the file")
    tags: Optional[list[str]] = Field(
        None, description="A list of tags associated with the file"
    )
    short_description: Optional[str] = Field(
        None, description="A short description of the file"
    )
    long_description: Optional[str] = Field(
        None, description="A long description of the file"
    )
    frozen: bool = Field(
        True, description="Indicates if the file is frozen (immutable)"
    )

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "sha256": self.sha256,
            "stat_json": self.stat_json.model_dump(),
            "path_json": self.path_json.model_dump(),
            "mime_type": self.mime_type,
            "tags": self.tags,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "frozen": self.frozen,
        }

    @field_validator("tags", mode="before")
    def validate_tags(cls, v):
        """
        validator for 'tags' field

        Ensures that all tags in the list are strings starting with '#', lowercase, and dash-separated.

        Args:
            v (list[str]): The list of tags to validate.

        Returns:
            list[str]: The validated list of tags.
        """
        if v is None:
            return v
        validated_tags = []
        for tag in v:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings.")
            tag = tag.strip().lower().replace(" ", "-")
            if not tag.startswith("#"):
                tag = f"#{tag}"
            validated_tags.append(tag)
        return validated_tags

    @field_validator("path_json", mode="before")
    def validate_path_json(cls, v):
        """
        Validator for 'path_json' field to ensure it is a PathModel instance.
        """
        try:
            if isinstance(v, FilePath):
                return v
            else:
                try:
                    return FilePath.model_validate(v, from_attributes=True)
                except Exception:
                    pass
            return FilePath.model_validate(v, from_attributes=True)
        except Exception as e:
            raise ValueError(f"Invalid path_json data: {e}")

    @field_validator("stat_json", mode="before")
    def validate_stat_json(cls, v):
        """
        Validator for 'stat_json' field to ensure it is a BaseFileStatModel instance.
        """
        try:
            if isinstance(v, BaseFileStat):
                return v
            elif isinstance(v, MacOSFileStat):
                return v
            elif isinstance(v, LinuxFileStat):
                return v
            elif isinstance(v, WindowsFileStat):
                return v
            else:
                return BaseFileStat.model_validate(v, from_attributes=True)
        except Exception as e:
            raise ValueError(f"Invalid stat_json data: {e}")

    @property
    def stat_model(self) -> BaseFileStat:
        """Return the FileStat model representation of the file's stat_json."""
        return BaseFileStat.model_validate(self.stat_json)

    @property
    def path_model(self) -> FilePath:
        """Return the FilePath model representation of the file's path_json."""
        return FilePath.model_validate(self.path_json)

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

    @property
    def Path(self) -> Path:
        return self.path_json.Path

    @property
    def suffix(self) -> str:
        return self.path_json.suffix

    @property
    def id(self) -> Optional[str]:
        return sha256(f"{self.Path}{self.sha256}".encode()).hexdigest()

    @property
    def uuid(self) -> Optional[str]:
        return sha256(
            f"{self.Path}{self.sha256}{self.stat_json.model_dump_json()}".encode()
        ).hexdigest()

    def is_empty(self) -> bool:
        return self.stat_json.st_size == 0

    @classmethod
    def populate(cls, file_path: Path) -> None:
        """
        Populate the model attributes based on the given file path.

        Args:
            file_path (Path): The path to the file.

        Returns:
            None
        """
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        return cls(
            sha256=get_file_sha256(file_path),
            stat_json=get_file_stat_model(file_path),
            path_json=get_path_model(file_path),
            mime_type=get_mime_type(file_path),
            tags=[],
            short_description=None,
            long_description=None,
            frozen=False,
        )

    model_config = ConfigDict(
        arbitrary_types_allowed=True, check_fields=False, from_attributes=True
    )


class BaseDirectory(BaseModel):
    """
    A Pydantic model to represent a directory with its path and file statistics.
    Attributes:
        path_json (PathModel): The path model of the directory.
        stat_json (BaseFileStatModel): The file statistics model of the directory.
        tags (Optional[list[str]]): A list of tags associated with the directory.
        short_description (Optional[str]): A short description of the directory.
        long_description (Optional[str]): A long description of the directory.
        frozen (bool): Indicates if the directory is frozen (immutable).
    """

    stat_json: BaseFileStat = Field(..., description="File statistics model")
    path_json: FilePath = Field(..., description="Path model of the file")
    tags: Optional[list[str]] = Field(
        None, description="A list of tags associated with the file"
    )
    short_description: Optional[str] = Field(
        None, description="A short description of the file"
    )
    long_description: Optional[str] = Field(
        None, description="A long description of the file"
    )
    frozen: bool = Field(
        True, description="Indicates if the file is frozen (immutable)"
    )

    @property
    def Path(self) -> Path:
        return self.path_json.Path

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        return {
            "stat_json": self.stat_json.model_dump(),
            "path_json": self.path_json.model_dump(),
            "tags": self.tags,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "frozen": self.frozen,
        }

    @property
    def name(self) -> str:
        """
        Return the name of the repository derived from the path.
        """
        return self.path_json.stem

    @property
    def id(self) -> str:
        return sha256(f"{self.name}{self.Path.as_posix()}".encode()).hexdigest()

    @property
    def uuid(self) -> str:
        return sha256(
            f"{self.name}{self.Path.as_posix()}{self.stat_json.model_dump_json()}".encode()
        ).hexdigest()

    @classmethod
    def populate(cls, dir_path: Path) -> "BaseDirectory":
        """
        Populate the model attributes based on the given directory path.

        Args:
            dir_path (Path): The path to the directory.

        Returns:
            BaseDirectory: An instance of BaseDirectory populated with directory data.
        """
        if isinstance(dir_path, str):
            dir_path = Path(dir_path).resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")
        if not issubclass(cls, BaseDirectory):
            raise TypeError("cls must be a subclass of BaseDirectory")
        instance = cls(
            stat_json=get_file_stat_model(dir_path),
            path_json=get_path_model(dir_path),
            tags=[],
            short_description=None,
            long_description=None,
            frozen=False,
        )
        return instance

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def is_empty(self) -> bool:
        """
        Check if the directory is empty (no files and no subdirectories).
        """
        return len(self.files) == 0 and len(self.directories) == 0


class GenericFile(BaseFileModel):
    """
    A Pydantic model to represent a generic file.
    """

    type: Literal["file"] = "file"


# endregion
# region Text File Models


class TextFileLine(BaseModel):
    """
    A Pydantic model to represent a line in a text file.

    Attributes:
        file_id (str): The ID of the text file.
        line (TextFileLine): A line in the text file.
    """

    id: Optional[int] = None
    file_id: str = Field(..., description="The ID of the text file")
    content: str = Field(..., description="The content of the line")
    line_number: Optional[int] = Field(None, description="The line number in the file")
    content_hash: Optional[str] = Field(
        None, description="SHA256 hash of the line content for deduplication"
    )

    @model_validator(mode="after")
    def compute_content_hash(self) -> "TextFileLine":
        """
        Compute the SHA256 hash of the line content for deduplication.
        """
        self.content_hash = sha256(self.content.encode()).hexdigest()
        return self

    @property
    def is_empty(self) -> bool:
        """Check if the line is empty or consists only of whitespace."""
        return self.content.strip() == ""

    @property
    def line_length(self) -> int:
        """Returns the length of the line content."""
        return len(self.content)


class BaseTextFile(BaseFileModel):
    """
    A Pydantic model to represent a text file with its lines.

    Attributes:
        sha256 (str): The SHA256 hash of the file.
        stat_json (BaseFileStatModel): The file statistics model.
        path_json (PathModel): The path model of the file.
        mime_type (Optional[str]): The MIME type of the file.
        tags (Optional[list[str]]): A list of tags associated with the file.
        short_description (Optional[str]): A short description of the file.
        long_description (Optional[str]): A long description of the file.
        frozen (bool): Indicates if the file is frozen (immutable).
        content (Optional[str]): The full content of the text file.
        lines_json (Optional[list[TextFileLine]]): A list of lines in the text file.
    """

    content: Optional[str] = None
    lines_json: Optional[list[TextFileLine]] = []

    @classmethod
    def populate(cls, file_path: Path) -> "BaseTextFile":
        """
        Populate the model attributes based on the given text file path.

        Args:
            file_path (Path): The path to the text file.

        Returns:
            BaseTextFile: An instance of BaseTextFile populated with file data.
        """
        instance = super().populate(file_path)
        # super() call checks for file existence and base file validations
        # here I am checking the file's suffix against the constants.MD_EXTENSIONS_LIST
        # via the utility function is_markdown_formattable()
        if not is_markdown_formattable(file_path):
            raise ValueError(f"File is not a text file: {file_path}")

        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

            content = "".join(lines).replace("\x00", "")

            lines_json = [
                TextFileLine(
                    file_id=instance.id,  # Access ID from the instance
                    content=line.rstrip("\n").rstrip("\r"),
                    line_number=i + 1,
                )
                for i, line in enumerate(lines)
            ]

        instance.content = content
        instance.lines_json = lines_json

        return instance

    @model_serializer(when_used="json")
    def serialize_model(self) -> dict:
        base_serialization = super().serialize_model()
        base_serialization.update(
            {
                "content": self.content,
                "lines_json": (
                    [line.model_dump() for line in self.lines_json]
                    if self.lines_json
                    else []
                ),
            }
        )
        return base_serialization

    @property
    def lines(self) -> list[TextFileLine]:
        """Returns a list of TextFileLine models representing the lines in the text file."""
        return self.lines_json if self.lines_json else []


# endregion
# region Scan Result Models


class BaseScanResult(BaseModel):
    """
    A Pydantic model to represent the result of a file system scan.

    Attributes:
        root (str): The root directory that was scanned.
        mode (Literal): The scanning mode used.
        started_at (Optional[datetime]): The timestamp when the scan started.
        ended_at (Optional[datetime]): The timestamp when the scan ended.
    """

    root: str = Field(..., description="The root directory that was scanned")
    mode: Literal[
        "git-local",
        "git-cloned",
        "image",
        "video",
        "database",
        "obsidian",
        "docs",
        "pdf",
        "all",
    ] = Field("all", description="The scanning mode used")
    started_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the scan started",
    )
    ended_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the scan ended"
    )

    @field_validator("mode", mode="before")
    def validate_type(cls, v: Union[str, None]) -> Optional[str]:
        if v not in [
            "git-local",
            "git-cloned",
            "image",
            "video",
            "database",
            "obsidian",
            "docs",
            "pdf",
            "all",
        ]:
            raise ValueError(f"Invalid scan mode: {v}")
        return v

    @property
    def Path(self) -> Path:
        return Path(self.root)

    @property
    def id(self) -> str:
        return sha256(f"{self.root}{self.mode}".encode()).hexdigest()

    @property
    def uuid(self) -> str:
        return sha256(f"{self.root}{self.mode}{self.started_at}".encode()).hexdigest()

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    @field_validator("started_at", mode="before")
    def validate_started_at(cls, v: Union[datetime, str, None]) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @field_validator("ended_at", mode="before")
    def validate_ended_at(cls, v: Union[datetime, str, None]) -> Optional[datetime]:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

    @model_serializer(when_used="json")
    def serialize_model(self):
        return {
            "scanned_on": self.scanned_on.isoformat() if self.scanned_on else None,
            "root": self.root,
            "mode": self.mode,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


# endregion

__all__ = [
    "FilePath",
    "BaseFileStat",
    "MacOSFileStat",
    "LinuxFileStat",
    "WindowsFileStat",
    "BaseFileModel",
    "GenericFile",
    "TextFileLine",
    "BaseTextFile",
    "BaseDirectory",
    "BaseScanResult",
]

#
