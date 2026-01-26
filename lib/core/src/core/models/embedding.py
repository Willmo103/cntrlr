# region Docstring
"""
core.models.embedding
Persistence and domain models for storing and managing text embeddings with vector representations.

Overview:
- Provides a SQLAlchemy entity for persisting text embeddings with their associated
    vector representations, enabling semantic search and similarity operations.
- Includes a corresponding Pydantic model for validation, serialization, and
    bidirectional conversion between persistence and domain layers.
- Utilizes pgvector extension for efficient vector storage and retrieval with HNSW indexing.

Contents:
- SQLAlchemy Entities:
    - EmbeddingEntity:
        Stores a single text embedding with its source reference, content, vector
        representation, and optional metadata. Uses polymorphic-style linking to
        associate embeddings with various source types (e.g., video frames, notes).
        Supports 768-dimensional vectors compatible with EmbeddingGemma models.
        Includes .model property to convert to Pydantic representation.

- Pydantic Models:
    - Embedding:
        Domain model representing a text embedding vector with full validation.
        Includes computed properties for vector_dimension and summary.
        Provides .entity property to convert to SQLAlchemy persistence layer.

Design Notes:
- The source_type and source_id columns provide flexible polymorphic linking, allowing
    embeddings to be associated with different entity types without rigid foreign keys.
- HNSW indexing on the vector column enables efficient approximate nearest neighbor
    searches for semantic similarity queries.
- The meta_data JSON column allows storing arbitrary contextual information (e.g.,
    timestamps, tags) for filtering and enhanced retrieval capabilities.
- Vector dimension (768) is configured for EmbeddingGemma models; adjust if using
    different embedding models with varying output dimensions.
- Bidirectional conversion between EmbeddingEntity and Embedding models follows the
    same pattern as other domain models in the codebase.
"""

# endregion
# region Imports
from typing import Any, Optional
from core.database import Base
from pgvector.sqlalchemy import VECTOR
from pydantic import BaseModel, Field
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column


# endregion
# region Sqlalchemy Model
class EmbeddingEntity(Base):
    """
    Model representing a text embedding vector.
    Attributes:
        id (int): Primary key.
        source_type (str): Type of the source (e.g., 'video_frame', 'note').
        source_id (str): Identifier of the source item.
        content (str): The text content that generated the embedding.
        vector (list[float]): The embedding vector.
        meta_data (dict): Additional metadata for filtering or context.
    """

    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Polymorphic-style linking (Flexible for Videos, Notes, etc.)
    # e.g., source_type="video_frame", source_id="20260108_..."
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[str] = mapped_column(String(255), index=True)

    # The actual text content that generated this vector
    content: Mapped[str] = mapped_column(Text)

    # The Vector (768 dim for EmbeddingGemma)
    # indexed=True creates an HNSW index for fast retrieval
    vector: Mapped[list[float]] = mapped_column(VECTOR(768), index=True)

    # Metadata for filtering (e.g., {"timestamp": "0:02:14", "tags": ["saw", "loud"]})
    meta_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Database Timestamps
    added_at: Mapped[Optional[Any]] = mapped_column(String, nullable=True, index=True)
    updated_at: Mapped[Optional[Any]] = mapped_column(String, nullable=True, index=True)

    def __repr__(self):
        return f"<Embedding(source={self.source_type}:{self.source_id})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmbeddingEntity):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def model(self) -> "Embedding":
        return Embedding(
            id=self.id,
            source_type=self.source_type,
            source_id=self.source_id,
            content=self.content,
            vector=self.vector,
            meta_data=self.meta_data,
        )

    @property
    def dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "content": self.content,
            "vector": self.vector,
            "meta_data": self.meta_data,
            "added_at": self.added_at,
            "updated_at": self.updated_at,
        }


# endregion
# region Pydantic Model
class Embedding(BaseModel):
    """
    Pydantic model representing a text embedding vector.
    Attributes:
        source_type (str): Type of the source (e.g., 'video_frame', 'note').
        source_id (str): Identifier of the source item.
        content (str): The text content that generated the embedding.
        vector (list[float]): The embedding vector.
        meta_data (dict): Additional metadata for filtering or context.
    """

    id: Optional[int] = Field(None, description="Primary key of the embedding")
    source_type: str = Field(
        ..., description="Type of the source (e.g., 'video_frame', 'note')"
    )
    source_id: str = Field(..., description="Identifier of the source item")
    content: str = Field(
        ..., description="The text content that generated the embedding"
    )
    vector: list[float] = Field(..., description="The embedding vector")
    meta_data: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata for filtering or context"
    )

    @property
    def entity(self) -> EmbeddingEntity:
        return EmbeddingEntity(
            id=self.id if self.id is not None else None,
            source_type=self.source_type,
            source_id=self.source_id,
            content=self.content,
            vector=self.vector,
            meta_data=self.meta_data,
        )

    @property
    def vector_dimension(self) -> int:
        """Return the dimension of the embedding vector."""
        return len(self.vector)

    @property
    def summary(self) -> dict[str, Any]:
        """Return a summary dictionary of the Embedding."""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "content_snippet": (
                self.content[:50] + "..." if len(self.content) > 50 else self.content
            ),
            "vector_dimension": self.vector_dimension,
            "meta_data": self.meta_data,
        }


# endregion

__all__ = ["EmbeddingEntity", "Embedding"]
