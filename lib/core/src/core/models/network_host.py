# region Docstring
"""
core.models.network_host
Persistence and domain models for indexing and working with network hosts.
Overview:
- Provides SQLAlchemy entities to persist network host information including
    hostname, IP address, MAC address, device type, and notes.
- Provides Pydantic models mirroring the persisted entities for safe I/O, validation,
    and serialization.
Contents:
- SQLAlchemy entities:
    - NetworkHostEntity:
        Persists a single network host with hostname, IP address, MAC address,
        device type, and notes. Includes helpers for equality (based on IP or MAC),
        hashing, and conversion to a NetworkHost Pydantic model via the .model property.
- Pydantic models:
    - NetworkHost:
        A domain model representing a single network host. Includes hostname, IP address,
        MAC address, device type, notes, and timestamp fields. Added/updated timestamps
        are parsed from ISO strings and serialized back to ISO strings.
Design notes:
- .model property on the SQLAlchemy entity provides an immediate conversion to the Pydantic
    model for safe I/O layers.
- Pydantic validators and serializers normalize timestamps (ISO 8601) and flexible input
    shapes.
- Equality comparison on NetworkHostEntity is based on IP address or MAC address matching,
    reflecting that either can uniquely identify a network host.
- The model uses ConfigDict with from_attributes=True to enable ORM mode compatibility.
"""

# endregion
# region Imports
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base

# endregion
# region SQLAlchemy Model


class NetworkHostEntity(Base):
    """
    Model representing a network host.
    Attributes:
        id (int): Primary key.
        hostname (str): The hostname of the network host.
        ip_address (str): The IP address of the network host.
        mac_address (str): The MAC address of the network host.
        device_type (str): The type of device (e.g., 'router', 'switch', 'server').
        notes (str): Additional notes about the network host.
    """

    __tablename__ = "network_hosts"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )  # noqa: E501
    hostname: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=True)
    device_type: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)

    # timestamps
    # In NetworkHost and ScanRoot
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<NetworkHost(id={self.id}, hostname='{self.hostname}', ip_address='{self.ip_address}', mac_address='{self.mac_address}', device_type='{self.device_type}')>"  # noqa: E501

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NetworkHostEntity):
            return NotImplemented

        return (
            self.ip_address == other.ip_address
            or self.mac_address == other.mac_address  # noqa: E501
        )

    def __hash__(self) -> int:
        return hash((self.ip_address, self.mac_address))

    @property
    def model(self) -> "NetworkHost":
        """Return the Pydantic model representation of the network host."""
        return NetworkHost.model_validate(
            {
                "id": self.id,
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "mac_address": self.mac_address,
                "device_type": self.device_type,
                "notes": self.notes,
            }
        )

    @property
    def dict(self) -> dict[str, Optional[str]]:
        return {
            "id": self.id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "device_type": self.device_type,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# endregion
# region Pydantic Model


class NetworkHost(BaseModel):
    """
    Database schema for a network host.
    Attributes:
        id (Optional[int]): The unique identifier of the network host.
        hostname (str): The hostname of the network host.
        ip_address (str): The IP address of the network host.
        mac_address (Optional[str]): The MAC address of the network host.
        device_type (Optional[str]): The type of device.
        notes (Optional[str]): Additional notes about the network host.
    """

    id: Optional[int] = Field(
        None, description="The unique identifier of the network host"
    )
    hostname: Optional[str] = Field(
        ..., max_length=255, description="The hostname of the network host"
    )
    ip_address: Optional[str] = Field(
        ..., max_length=45, description="The IP address of the network host"
    )
    mac_address: Optional[str] = Field(
        None, max_length=17, description="The MAC address of the network host"
    )
    device_type: Optional[str] = Field(
        None, max_length=100, description="The type of device"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional notes about the network host",
    )
    added_at: Optional[datetime] = Field(
        None, description="Timestamp when the network host was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when the network host was last updated"
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

    model_config = ConfigDict(from_attributes=True)

    @property
    def entity(self) -> NetworkHostEntity:
        return NetworkHostEntity(
            id=self.id if self.id is not None else None,
            hostname=self.hostname,
            ip_address=self.ip_address,
            mac_address=self.mac_address,
            device_type=self.device_type,
            notes=self.notes,
        )


# endregion

__all__ = ["NetworkHostEntity", "NetworkHost"]
