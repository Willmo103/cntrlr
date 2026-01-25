# region Docstring
"""
core.models.embedding
Persistence model for storing and managing text embeddings with vector representations.

Overview:
- Provides a SQLAlchemy entity for persisting text embeddings with their associated
    vector representations, enabling semantic search and similarity operations.
- Utilizes pgvector extension for efficient vector storage and retrieval with HNSW indexing.

Contents:
- SQLAlchemy entities:
    - EmbeddingEntity:
        Stores a single text embedding with its source reference, content, vector
        representation, and optional metadata. Uses polymorphic-style linking to
        associate embeddings with various source types (e.g., video frames, notes).
        Supports 768-dimensional vectors compatible with EmbeddingGemma models.

Design notes:
- The source_type and source_id columns provide flexible polymorphic linking, allowing
    embeddings to be associated with different entity types without rigid foreign keys.
- HNSW indexing on the vector column enables efficient approximate nearest neighbor
    searches for semantic similarity queries.
- The meta_data JSON column allows storing arbitrary contextual information (e.g.,
    timestamps, tags) for filtering and enhanced retrieval capabilities.
- Vector dimension (768) is configured for EmbeddingGemma models; adjust if using
    different embedding models with varying output dimensions.
"""
from core.database import Base

# endregion
# region Imports
from pgvector.sqlalchemy import VECTOR
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

    def __repr__(self):
        return f"<Embedding(source={self.source_type}:{self.source_id})>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmbeddingEntity):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# endregion

__all__ = ["EmbeddingEntity"]
