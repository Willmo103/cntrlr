
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from core.database import Base
from sqlite_utils import Database


class URLFetch(BaseModel):
    """
    Pydantic model representing the URL fetch results.

    Attributes:
        url (str): The URL that was fetched.
        result (int): The result code of the URL fetch operation.
        html_content (Optional[str]): The fetched HTML content from the URL.
        error_message (Optional[str]): Error message if the fetch operation failed.
        first_seen (Optional[datetime]): Timestamp when the URL was first seen.
        last_updated (Optional[datetime]): Timestamp when the URL was last updated.
    """
    url: str = Field(..., description="The URL that was fetched.")
    result: int = Field(
        ..., description="The result code of the URL fetch operation.")
    html_content: Optional[str] = Field(
        None, description="The fetched HTML content from the URL.")
    error_message: Optional[str] = Field(
        None, description="Error message if the fetch operation failed.")
    first_seen: Optional[datetime] = Field(
        None, description="Timestamp when the URL was first seen.")
    last_updated: Optional[datetime] = Field(
        None, description="Timestamp when the URL was last updated.")

    @property
    def id(self) -> Optional[int]:
        """Get the ID of the URL fetch result, if available."""
        return hash(self.url)


    def store_in_db(self, db: Database) -> None:
        """Store the URL fetch result in the sqlite_utils database."""
        table = db.table("url_fetches", pk="url", columns={
            "id": int,
            "url": str,
            "result": int,
            "html_content": str,
            "error_message": str,
            "first_seen": datetime,
            "last_updated": datetime,
        })
        table.insert({
            "id": self.id,
            "url": self.url,
            "result": self.result,
            "html_content": self.html_content,
            "error_message": self.error_message,
            "first_seen": self.first_seen or datetime.utcnow(),
            "last_updated": self.last_updated or datetime.utcnow(),
        }, replace=True)

    @classmethod
    def from_db(cls, db: Database, url: str) -> Optional["URLFetch"]:
        """Retrieve a URL fetch result from the sqlite_utils database by its URL."""
        table = db.table("url_fetches")
        row = table.get(url)
        if row:
            return cls(
                url=row["url"],
                result=row["result"],
                html_content=row.get("html_content"),
                error_message=row.get("error_message"),
                first_seen=row.get("first_seen"),
                last_updated=row.get("last_updated"),
            )
        return None

class UploadedDocument(BaseModel):
    """
    Pydantic model representing a file upload stored in a sqlite_utils database.

    Attributes:
        id: Optional[str]: The unique identifier for the uploaded document (Content Hash + mime_type).
        filename: str: The original filename of the uploaded document.
        mime_type: str: The MIME type of the uploaded document.
        content_bytes: bytes: The raw content of the uploaded document.
        uploaded_at: Optional[datetime]: Timestamp when the document was uploaded.
    """

    id: Optional[str] = Field(
        None, description="The unique identifier for the uploaded document (Content Hash + mime_type)."
    )
    filename: str = Field(..., description="The original filename of the uploaded document.")
    mime_type: str = Field(..., description="The MIME type of the uploaded document.")
    content_bytes: bytes = Field(..., description="The raw content of the uploaded document.")
    uploaded_at: Optional[datetime] = Field(
        None, description="Timestamp when the document was uploaded."
    )

    def store_in_db(self, db: Database) -> None:
        """Store the uploaded document in the sqlite_utils database."""
        table = db.table("uploaded_documents", pk="id", columns={
            "filename": str,
            "mime_type": str,
            "content_bytes": bytes,
            "uploaded_at": datetime,
        })
        table.insert({
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "content_bytes": self.content_bytes,
            "uploaded_at": self.uploaded_at or datetime.utcnow(),
        }, replace=True)

    @classmethod
    def from_db(cls, db: Database, document_id: str) -> Optional["UploadedDocument"]:
        """Retrieve an uploaded document from the sqlite_utils database by its ID."""
        table = db.table("uploaded_documents")
        row = table.get(document_id)
        if row:
            return cls(
                id=row["id"],
                filename=row["filename"],
                mime_type=row["mime_type"],
                content_bytes=row["content_bytes"],
                uploaded_at=row.get("uploaded_at"),
            )
        return None
