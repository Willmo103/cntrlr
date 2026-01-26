# region Docstring
"""
core.models.tts
Persistence and domain models for Text-to-Speech (TTS) history tracking.
Overview:
- Provides SQLAlchemy entity to persist TTS generation history including input text,
    voice configuration, audio output, and processing metadata.
- Provides Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.
Contents:
- SQLAlchemy entities:
    - TTSHistoryEntity:
        Persists a single TTS generation record with input text, voice/model used,
        raw audio binary data, server processing URL, and optional S3 bucket storage path.
        Includes helpers for equality, hashing, and conversion to the TTSHistory Pydantic model
        via the .model property.
- Pydantic models:
    - TTSHistory:
        A domain model representing a TTS history record. Includes input text, voice
        configuration, creation timestamp, optional audio bytes, server URL, and bucket path.
        Provides JSON-oriented serialization with ISO 8601 timestamp formatting.
Design notes:
- .model property on SQLAlchemy entity provides immediate conversion to Pydantic
    model for safe I/O layers.
- ConfigDict with from_attributes=True enables ORM mode for seamless entity-to-model
    conversion.
- Audio data stored as LargeBinary allows direct database storage of generated speech,
    with optional S3 bucket_path for external storage references.
- Timestamps are server-generated using func.now() for consistency.

"""
# endregion
# region Imports
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_serializer
from sqlalchemy import DateTime, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


# endregion


# region TTS History Model
class TTSHistoryEntity(Base):
    """
    Records history of TTS generations, including the raw audio binary.
    Matches the 'tts_history' table schema.

    Attributes:
        id (int): Primary key.
        text (str): The input text that was converted to speech.
        voice (str): The voice/model used for TTS.
        created_at (datetime): Timestamp of when the TTS was generated.
        response_bytes (bytes): The raw audio data generated.
        server_url (str): The server URL where the TTS was processed.
        bucket_path (str): S3 bucket path if the audio is stored there.
    """

    __tablename__ = "tts_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    voice: Mapped[str] = mapped_column(Text, nullable=True)  # The model name
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    response_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    server_url: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # Where it was processed
    bucket_path: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # S3 bucket path if applicable

    def __repr__(self) -> str:
        return f"<TTSHistory(id={self.id}, text='{self.text[:20]}...', voice='{self.voice}')>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TTSHistoryEntity):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def model(self) -> "TTSHistory":
        """Convert the ORM entity to a Pydantic model."""
        return TTSHistory(
            id=self.id,
            text=self.text,
            voice=self.voice,
            created_at=self.created_at,
            response_bytes=self.response_bytes,
            server_url=self.server_url,
            bucket_path=self.bucket_path,
        )

    @property
    def audio(self) -> Optional[bytes]:
        """Get the raw audio bytes."""
        return self.response_bytes


# endregion


# region Pydantic Model for TTS History
class TTSHistory(BaseModel):
    """
    Pydantic model representing a TTS history record.

    Attributes:
        id (int): Primary key.
        text (str): The input text that was converted to speech.
        voice (Optional[str]): The voice/model used for TTS.
        created_at (datetime): Timestamp of when the TTS was generated.
        response_bytes (Optional[bytes]): The raw audio data generated.
        server_url (Optional[str]): The server URL where the TTS was processed.
        bucket_path (Optional[str]): S3 bucket path if the audio is stored there.
    """

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(None, description="Primary key")
    text: str = Field(..., description="The input text that was converted to speech")
    voice: Optional[str] = Field(None, description="The voice/model used for TTS")
    created_at: datetime = Field(
        ..., description="Timestamp of when the TTS was generated"
    )
    response_bytes: Optional[bytes] = Field(
        None, description="The raw audio data generated"
    )
    server_url: Optional[str] = Field(
        None, description="The server URL where the TTS was processed"
    )
    bucket_path: Optional[str] = Field(
        None, description="S3 bucket path if the audio is stored there"
    )

    @model_serializer("json")
    def serialize_model(self) -> dict:
        return {
            **super().serialize_model(),
            "created_at": self.created_at.isoformat(),
        }


# endregion

__all__ = ["TTSHistoryEntity", "TTSHistory"]
