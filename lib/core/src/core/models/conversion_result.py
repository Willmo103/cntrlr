# region Docstring
"""
core.models.conversion_result
Persistence model for storing document conversion results.
Overview:
- Provides a SQLAlchemy entity to persist the results of document conversion processes,
    including Markdown and plain text output formats.
- Stores references to S3 storage locations for full JSON conversion data.
Contents:
- SQLAlchemy entities:
    - ConversionResult:
        Persists a single conversion result with a unique identifier (uuid), optional
        Markdown and plain text content, and an S3 key reference to the full JSON
        representation. Includes equality and hash implementations based on uuid and
        S3 key for deduplication and comparison.
    - id (int): Auto-incrementing primary key.
    - uuid (str): Unique identifier for the conversion result, ensuring idempotency
        and external reference capability.
    - markdown (Optional[str]): The converted content in Markdown format.
    - text (Optional[str]): The converted content in plain text format.
    - s3_json_key (str): S3 object key where the complete JSON conversion result
        is stored for retrieval.
    - created_at (datetime): Server-side timestamp indicating when the record was created.
Design notes:
- The uuid field provides a stable external identifier for referencing conversion results
    across systems and API calls.
- Markdown and text fields allow quick access to common output formats without requiring
    S3 retrieval for simple use cases.
- The s3_json_key field enables storage of large or complex conversion results in S3,
    keeping the database lightweight while preserving full fidelity data.
- Equality is determined by uuid, markdown, text, and s3_json_key to support comparison
    of conversion outputs.
- Hash is based on uuid and s3_json_key for efficient set/dict operations.
"""
# endregion
# region Imports
from datetime import datetime
from typing import Optional

from core.database import Base
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


# endregion
# region Sqlalchemy Model
class ConversionResultEntity(Base):
    """
    Model representing the result of a conversion process.
    Attributes:
        id (int): Primary key.
        uuid (str): Unique identifier for the conversion result.
        markdown (Optional[str]): Converted content in Markdown format.
        text (Optional[str]): Converted content in plain text format.
        s3_json_key (str): S3 key where the JSON representation is stored.
        created_at (datetime): Timestamp when the record was created.
        updated_at (datetime): Timestamp when the record was last updated.
    """

    __tablename__ = "conversion_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    markdown: Mapped[str] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(String, nullable=True)
    s3_json_key: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ConversionResult(id={self.id}, uuid='{self.uuid}')>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConversionResultEntity):
            return NotImplemented

        return (
            self.uuid == other.uuid
            and self.markdown == other.markdown
            and self.text == other.text
            and self.s3_json_key == other.s3_json_key
        )

    def __hash__(self) -> int:
        return hash((self.uuid, self.s3_json_key))

    @property
    def model(self) -> "ConversionResult":
        return ConversionResult(
            id=self.id,
            uuid=self.uuid,
            markdown=self.markdown,
            text=self.text,
            s3_json_key=self.s3_json_key,
        )

    @property
    def dict(self) -> dict[str, Optional[str]]:
        return {
            "id": self.id,
            "uuid": self.uuid,
            "markdown": self.markdown,
            "text": self.text,
            "s3_json_key": self.s3_json_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# endregion
# region Pydantic Model
class ConversionResult(BaseModel):
    id: Optional[int] = Field(None, description="Primary key of the conversion result")
    uuid: str = Field(..., description="Unique identifier for the conversion result")
    markdown: Optional[str] = Field(
        None, description="Converted content in Markdown format"
    )
    text: Optional[str] = Field(
        None, description="Converted content in plain text format"
    )
    s3_json_key: str = Field(
        ..., description="S3 key where the JSON representation is stored"
    )

    @property
    def entity(self) -> ConversionResultEntity:
        return ConversionResultEntity(
            id=self.id if self.id is not None else None,
            uuid=self.uuid,
            markdown=self.markdown,
            text=self.text,
            s3_json_key=self.s3_json_key,
        )


# endregion
__all__ = ["ConversionResultEntity"]
