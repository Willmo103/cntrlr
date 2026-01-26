# region Docstring
"""
core.models.log_entry
Persistence model for system log entries.
Overview:
- Provides a SQLAlchemy entity to persist system log entries with timestamp,
    log level, originating service, and message content.
Contents:
- SQLAlchemy entities:
    - LogEntryEntity:
        Persists a single system log entry with automatic timestamping. Includes
        log level categorization (INFO, ERROR, WARNING), service identification,
        and the log message. Provides equality comparison and hashing based on
        all log attributes for deduplication purposes.
Design notes:
- Timestamps are stored with timezone awareness and default to the current time
    on the database server.
- The service field allows filtering logs by component (e.g., 'controller',
    'converter') for easier debugging and monitoring.
- Equality and hashing are based on all log attributes to support set operations
    and duplicate detection.
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
class LogEntryEntity(Base):
    """
    Model representing a system log entry.

    Attributes:
        id (int): Primary key.
        timestamp (datetime): Timestamp of the log entry.
        level (str): Log level (e.g., INFO, ERROR, WARNING).
        service (str): Service that generated the log (e.g., 'controller', 'converter').
        message (str): Log message.
    """

    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    level: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # INFO, ERROR, WARNING
    service: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'controller', 'converter'
    message: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<LogEntry(id={self.id}, level='{self.level}', service='{self.service}')>"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogEntryEntity):
            return NotImplemented

        return (
            self.timestamp == other.timestamp
            and self.level == other.level
            and self.service == other.service
            and self.message == other.message
        )

    def __hash__(self) -> int:
        return hash((self.timestamp, self.level, self.service, self.message))

    @property
    def model(self) -> "LogEntry":
        from core.models import LogEntry

        return LogEntry(
            id=self.id,
            timestamp=self.timestamp,
            level=self.level,
            service=self.service,
            message=self.message,
        )

    @property
    def dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level,
            "service": self.service,
            "message": self.message,
        }


# endregion
# region Pydantic Model
class LogEntry(BaseModel):
    """
    Pydantic model representing a system log entry.

    Attributes:
        id (Optional[int]): Primary key.
        timestamp (Optional[datetime]): Timestamp of the log entry.
        level (str): Log level (e.g., INFO, ERROR, WARNING).
        service (str): Service that generated the log (e.g., 'controller', 'converter').
        message (str): Log message.
    """

    id: Optional[int] = Field(None, description="Primary key of the log entry")
    timestamp: Optional[datetime] = Field(
        None, description="Timestamp of the log entry"
    )
    level: str = Field(..., description="Log level (e.g., INFO, ERROR, WARNING)")
    service: str = Field(
        ...,
        description="Service that generated the log (e.g., 'controller', 'converter')",
    )
    message: str = Field(..., description="Log message")

    @property
    def entity(self) -> LogEntryEntity:
        return LogEntryEntity(
            id=self.id if self.id is not None else None,
            timestamp=self.timestamp if self.timestamp is not None else func.now(),
            level=self.level,
            service=self.service,
            message=self.message,
        )


__all__ = ["LogEntryEntity"]
