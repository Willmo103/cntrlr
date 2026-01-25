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

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


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


# endregion

__all__ = ["LogEntryEntity"]
