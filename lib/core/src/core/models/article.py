# region Docstring
"""
core.models.article
Persistence and domain models for storing and working with web articles.
Overview:
- Provides SQLAlchemy entity to persist articles with URL, HTML content, Markdown
    conversions, AI-generated summaries, and associated metadata.
- Provides Pydantic model mirroring the persisted entity for safe I/O, validation,
    and serialization.
Contents:
- SQLAlchemy entities:
    - ArticleEntity:
        Persists a single article with URL, raw HTML content, converted Markdown content,
        AI-cleaned Markdown content, AI-generated summary, tags, and timestamps. Includes
        a .model property to convert to the Article Pydantic model. Implements equality
        and hashing based on URL for deduplication.
- Pydantic models:
    - Article:
        A domain model representing a single article. Includes URL, HTML content,
        Markdown conversions (raw and AI-cleaned), AI-generated summary, tags, and
        added/updated timestamps. Validators parse ISO strings for timestamps and
        handle flexible tag input (strings, sets, tuples). Serializers return ISO
        formatted timestamps and properly formatted tag lists.
Design notes:
- .model property on SQLAlchemy entity provides immediate conversion to Pydantic
    model for safe I/O layers.
- Pydantic validators and serializers normalize timestamps (ISO 8601) and flexible
    input shapes for tags (comma-separated strings, sets, tuples, lists).
- URL-based equality and hashing on ArticleEntity ensures consistent deduplication
    when processing articles from the same source.
- Optional fields allow for incremental population as articles progress through
    processing stages (fetch → convert → clean → summarize).
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
class ArticleEntity(Base):
    """
    Model representing an article.
    Attributes:
        id (int): Primary key.
        url (str): The URL of the article.
        html_content (str): The raw HTML content of the article.
        markdown_content (str): The converted Markdown content of the article.
        cleaned_markdown_content (str): The cleaned Markdown content (AI-processed).
        article_summary Optional[str]: AI-generated summary of the article.
        tags (List[str]): Tags associated with the article.
        added_at (datetime): Timestamp of when the article was added.
        updated_at (datetime): Timestamp of the last update to the article.
    """

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    html_content: Mapped[str] = mapped_column(String, nullable=False)
    markdown_content: Mapped[str] = mapped_column(String, nullable=True)
    cleaned_markdown_content: Mapped[str] = mapped_column(String, nullable=True)
    article_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(String, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # DB Record Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, url='{self.url}')>"

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArticleEntity):
            return NotImplemented

        return self.url == other.url

    @property
    def model(self) -> "Article":
        """Convert the ORM entity to a Pydantic model."""
        return Article(
            id=self.id,
            url=self.url,
            html_content=self.html_content,
            markdown_content=self.markdown_content,
            cleaned_markdown_content=self.cleaned_markdown_content,
            article_summary=self.article_summary,
            tags=self.tags,
            added_at=self.added_at,
            updated_at=self.updated_at,
        )

    @property
    def dict(self) -> dict[str, Optional[object]]:
        """Return a dictionary representation of the ArticleEntity."""
        return {
            "id": self.id,
            "url": self.url,
            "html_content": self.html_content,
            "markdown_content": self.markdown_content,
            "cleaned_markdown_content": self.cleaned_markdown_content,
            "article_summary": self.article_summary,
            "tags": self.tags,
            "added_at": self.added_at,
            "updated_at": self.updated_at,
        }


# endregion
# region Pydantic Model
class Article(BaseModel):
    """
    Pydantic model representing an article.
    Attributes:
        id (Optional[int]): The unique identifier of the article.
        url (str): The URL of the article.
        html_content (str): The raw HTML content of the article.
        markdown_content (Optional[str]): The converted Markdown content of the article.
        cleaned_markdown_content (Optional[str]): The cleaned Markdown content (AI-processed).
        article_summary (Optional[str]): AI-generated summary of the article.
        tags (Optional[List[str]]): Tags associated with the article.
        added_at (datetime): Timestamp of when the article was added.
        updated_at (Optional[datetime]): Timestamp of the last update to the article.
    """

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(default=None)
    url: str = Field(..., description="The URL of the article")
    html_content: Optional[str] = Field(
        default=None, description="The raw HTML content of the article"
    )
    markdown_content: Optional[str] = Field(
        default=None, description="The converted Markdown content of the article"
    )
    cleaned_markdown_content: Optional[str] = Field(
        default=None, description="The cleaned Markdown content (AI-processed)"
    )
    article_summary: Optional[str] = Field(
        default=None, description="AI-generated summary of the article"
    )
    tags: Optional[list[str]] = Field(
        default=None, description="Tags associated with the article"
    )
    added_at: Optional[datetime] = Field(
        None, description="Timestamp of when the article was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the last update to the article"
    )

    @field_serializer("tags")
    def serialize_tags(self, tags: Optional[list[str]]) -> Optional[list[str]]:
        if tags is None:
            return None
        return tags

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

    @field_validator("tags", mode="before")
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if isinstance(v, str):
            try:
                return v.split(",") if v else []
            except Exception:
                return []
        if isinstance(v, set) or isinstance(v, tuple):
            return list(v)
        return v

    @property
    def entity(self) -> ArticleEntity:
        return ArticleEntity(
            id=self.id if self.id is not None else None,
            url=self.url,
            html_content=self.html_content if self.html_content is not None else "",
            markdown_content=self.markdown_content,
            cleaned_markdown_content=self.cleaned_markdown_content,
            article_summary=self.article_summary,
            tags=self.tags,
        )


# endregion

__all__ = ["ArticleEntity", "Article"]
