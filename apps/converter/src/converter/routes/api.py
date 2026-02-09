# region Docstrings
""" """

# endregion
# region Imports

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import httpx
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.document_extractor import DocumentExtractor
from docling_core.types import DoclingDocument
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    PipelineOptions

)
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

# from core.models.conversion_result import ConversionResultEntity, ConversionResult
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlite_utils import Database

from core.database import Base
from core.utils import get_time, get_time_iso

from ..config import CONVERTED_STORAGE_PATH, INPUT_STORAGE_PATH
from ..logger import logger as _logger

# endregion
# region Storage Paths

input_html_storage = INPUT_STORAGE_PATH / "html"
"""Path to raw HTML storage directory."""
input_doc_storage = INPUT_STORAGE_PATH / "uploaded"
"""Path to uploaded document storage directory."""
docling_document_storage = CONVERTED_STORAGE_PATH / "dl_documents"
"""Path where JSON Docling documents are stored."""
db: Database = Database(CONVERTED_STORAGE_PATH / "converter_data.db")
"""SQLite Utils Database instance for converter data storage."""

docling_document_storage.mkdir(parents=True, exist_ok=True)
input_html_storage.mkdir(parents=True, exist_ok=True)
input_doc_storage.mkdir(parents=True, exist_ok=True)

pipeline_options = PipelineOptions()
pipeline_options.accelerator_options = AcceleratorOptions(
    num_threads=6, device=AcceleratorDevice.AUTO
)

doc_converter = DocumentConverter(
    allowed_formats=[
        InputFormat.PDF,
        InputFormat.IMAGE,
        InputFormat.DOCX,
        InputFormat.HTML,
        InputFormat.PPTX,
        InputFormat.ASCIIDOC,
        InputFormat.CSV,
        InputFormat.MD,
    ],
    format_options={
        InputFormat.IMAGE:
    }
)
extractor = DocumentExtractor(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])

# endregion
# region API Models


class URLFetch(BaseModel):
    """
    Pydantic model representing the URL fetch results.

    Attributes:
        url (str): The URL that was fetched.
        result (int): The result code of the URL fetch operation.
        storage_path (str): The local storage path where the fetched HTML content is saved.
        error_message (Optional[str]): Error message if the fetch operation failed.
        first_seen (Optional[datetime]): Timestamp when the URL was first seen.
        last_updated (Optional[datetime]): Timestamp when the URL was last updated.
    """

    url: str = Field(..., description="The URL that was fetched.")
    result: int = Field(..., description="The result code of the URL fetch operation.")
    storage_path: str = Field(
        ...,
        description="The local storage path where the fetched HTML content is saved.",
    )
    error_message: Optional[str] = Field(
        None, description="Error message if the fetch operation failed."
    )
    first_seen: Optional[datetime] = Field(
        None, description="Timestamp when the URL was first seen."
    )
    last_updated: Optional[datetime] = Field(
        None, description="Timestamp when the URL was last updated."
    )

    @field_validator("url")
    def validate_url(cls, v):
        """Validate that the URL is well-formed."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @model_validator(mode="before")
    def validate_result_and_error(cls, values):
        """Ensure that if result indicates an error, error_message is provided."""
        result = values.get("result")
        error_message = values.get("error_message")
        if result != 200 and not error_message:
            raise ValueError("Error message must be provided if result is not 200.")
        return values

    @model_validator(mode="before")
    def set_timestamps(cls, values):
        """Set first_seen and last_updated timestamps if not provided."""
        now = get_time()
        if not values.get("first_seen"):
            values["first_seen"] = now
        if not values.get("last_updated"):
            values["last_updated"] = now
        return values

    @property
    def id(self) -> Optional[str]:
        """Get the unique identifier for the URL fetch result."""

        hasher = hashlib.sha256()
        hasher.update(self.url.encode("utf-8"))
        return hasher.hexdigest()

    @property
    def Path(self) -> Path:
        """Get the storage path as a Path object."""
        return Path(self.storage_path)


class UploadedDocument(BaseModel):
    """
    Pydantic model representing a file upload stored in a sqlite_utils database.

    Attributes:
        filename: str: The original filename of the uploaded document.
        mime_type: str: The MIME type of the uploaded document.
        storage_path: str: The local storage path where the uploaded document is saved.
        uploaded_at: Optional[datetime]: Timestamp when the document was uploaded.
    """

    filename: str = Field(
        ..., description="The original filename of the uploaded document."
    )
    mime_type: str = Field(..., description="The MIME type of the uploaded document.")
    storage_path: str = Field(
        ..., description="The local storage path where the uploaded document is saved."
    )
    uploaded_at: Optional[datetime] = Field(
        None, description="Timestamp when the document was uploaded."
    )

    @property
    def id(self) -> Optional[str]:
        """Get the unique identifier for the uploaded document."""

        hasher = hashlib.sha256()
        hasher.update(self.content_bytes)
        hasher.update(self.mime_type.encode("utf-8"))
        return hasher.hexdigest()

    @property
    def Path(self) -> Path:
        """Get the storage path as a Path object."""
        return Path(self.storage_path)


class URLConversionRequest(BaseModel):
    url: str = Field(..., description="The URL of the document to be converted.")


class ConvertedDocument(BaseModel):
    """
    Pydantic model representing a converted document.

    Attributes:
        id: str: Unique identifier for the converted document.
        source_url: Optional[str]: The original URL of the document, if applicable.
        storage_path: str: The local storage path where the converted document is saved.
        conversion_time: Optional[datetime]: Timestamp when the conversion was performed.
    """

    source: Union[URLFetch, UploadedDocument] = Field(
        ..., description="The source of the document conversion."
    )
    document_json_path: Path = Field(
        ...,
        description="The local storage path where the converted document JSON is saved.",
    )
    conversion_time: datetime = Field(
        default=get_time(), description="Timestamp when the conversion was performed."
    )

    @property
    def id(self) -> Optional[str]:
        """Get the unique identifier for the converted document."""

        hasher = hashlib.sha256()
        hasher.update(self.source_id.encode("utf-8"))
        hasher.update(str(self.source_path).encode("utf-8"))
        hasher.update(str(self.document_json_path).encode("utf-8"))
        return hasher.hexdigest()

    @property
    def Document(self) -> DoclingDocument:
        """Load the converted document as a DoclingDocument instance."""
        try:
            return DoclingDocument.model_validate_json(
                self.document_json_path.read_text(encoding="utf-8")
            )
        except Exception as e:
            _logger.error(
                f"Error loading DoclingDocument from {self.document_json_path}: {e}"
            )
            raise ValueError(f"Failed to load DoclingDocument: {e}") from e

    @property
    def markdown(self) -> str:
        """Export the DoclingDocument to Markdown format."""
        try:
            doc = self.Document
            return doc.export_to_markdown()
        except Exception as e:
            _logger.error(
                f"Error exporting DoclingDocument to Markdown from {self.document_json_path}: {e}"
            )
            raise ValueError(
                f"Failed to export DoclingDocument to Markdown: {e}"
            ) from e

    @property
    def html(self) -> str:
        try:
            doc = self.Document
            return doc.export_to_html()
        except Exception as e:
            _logger.error(
                f"Error exporting DoclingDocument to HTML from {self.document_json_path}: {e}"
            )
            raise ValueError(f"Failed to export DoclingDocument to HTML: {e}") from e

    @property
    def doctags(self) -> list[str]:
        try:
            doc = self.Document
            return doc.export_to_doctags()
        except Exception as e:
            _logger.error(
                f"Error retrieving doctags from DoclingDocument at {self.document_json_path}: {e}"
            )
            raise ValueError(f"Failed to retrieve doctags: {e}") from e

    @property
    def text(self) -> list[str]:
        try:
            doc = self.Document
            return doc.export_to_text()
        except Exception as e:
            _logger.error(
                f"Error retrieving doc tokens from DoclingDocument at {self.document_json_path}: {e}"
            )
            raise ValueError(f"Failed to retrieve doc tokens: {e}") from e

    @property
    def sourcePath(self) -> Path:
        """Get the original source document path."""
        return self.source.Path

    @property
    def source_document(self) -> Optional[str]:
        """Get the original source document content."""
        try:
            return self.sourcePath.read_text(encoding="utf-8")
        except Exception as e:
            _logger.error(
                f"Error reading source document from {self.sourcePath}: {e}"
            )
            return None


# endregion
# region Helper Functions


async def handle_fetch_request(url: str) -> URLFetch:
    """Fetch a URL and store its HTML content locally."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

        timestamp = get_time().strftime("%Y%m%d%H%M%S")
        safe_filename = url.replace("://", "_").replace("/", "_")
        file_name = f"{safe_filename}_{timestamp}.html"
        file_path = input_html_storage / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        result = URLFetch(
            url=url,
            result=response.status_code,
            storage_path=str(file_path),
            first_seen=get_time(),
            last_updated=get_time(),
        )
        db["url_fetches"].upsert(result.model_dump(), pk="url")
        return result
    except httpx.HTTPError as e:
        _logger.error(f"HTTP error fetching URL {url}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e}") from e
    except Exception as e:
        _logger.error(f"Error fetching URL {url}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


async def handle_file_upload(request: Request) -> UploadedDocument:
    """Handle file upload and store the document locally."""
    try:
        form = await request.form()
        upload_file = form.get("file")
        if not upload_file:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        content = await upload_file.read()
        timestamp = get_time().strftime("%Y%m%d%H%M%S")
        safe_filename = upload_file.filename.replace("/", "_")
        file_name = f"{safe_filename}_{timestamp}"
        file_path = input_doc_storage / file_name

        with open(file_path, "wb") as f:
            f.write(content)

        uploaded_doc = UploadedDocument(
            filename=upload_file.filename,
            mime_type=upload_file.content_type,
            storage_path=str(file_path),
            uploaded_at=get_time(),
        )
        db["uploaded_documents"].upsert(uploaded_doc.model_dump(), pk="storage_path")
        return uploaded_doc
    except Exception as e:
        _logger.error(f"Error handling file upload: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


async def handle_conversion(
    source: Union[URLFetch, UploadedDocument],
) -> ConvertedDocument:
    """Handle document conversion using Docling."""
    try:
        if isinstance(source, URLFetch):
            source_path = Path(source.storage_path)
        elif isinstance(source, UploadedDocument):
            source_path = Path(source.storage_path)
        else:
            raise ValueError("Unsupported source type for conversion.")

        docling_doc = doc_converter.convert(str(source_path))
        timestamp = get_time().strftime("%Y%m%d%H%M%S")
        safe_filename = source_path.stem.replace("/", "_")
        json_file_name = f"{safe_filename}_{timestamp}.json"
        json_file_path = docling_document_storage / json_file_name

        with open(json_file_path, "w", encoding="utf-8") as f:
            f.write(docling_doc.model_dump_json())

        converted_doc = ConvertedDocument(
            source=source,
            document_json_path=json_file_path,
            conversion_time=get_time(),
        )
        db["converted_documents"].upsert(converted_doc.model_dump(), pk="id")
        return converted_doc
    except Exception as e:
        _logger.error(f"Error handling document conversion: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


# endregion
# region API Router and Endpoints

conversion_api = APIRouter(prefix="/api", tags=["conversion"])


@conversion_api.get("/", summary="Conversion API Root")
async def conversion_api_root(req: Request) -> dict[str, str]:
    """Root endpoint for the Conversion API."""
    try:
        _logger.info(
            "Conversion API root endpoint accessed by: {} at {}".format(
                req.client.host, get_time_iso()
            )
        )
        _logger.debug("Request details: {}".format(req))
        return {"message": "Conversion API is operational."}
    except Exception as e:
        _logger.error(
            "Error in conversion_api_root: {} at {}".format(e, get_time_iso()),
            exc_info=True,
            stack_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


@conversion_api.post(
    "/convert/web", summary="Convert Web Document", response_model=URLFetch
)
async def convert_web_document(request: URLConversionRequest) -> URLFetch:
    """Endpoint to convert a web document given its URL."""
    try:
        _logger.info(
            "Convert web document endpoint accessed for URL: {} at {}".format(
                request.url, get_time_iso()
            )
        )
        # Placeholder for actual conversion logic

        result: URLFetch = await handle_fetch_request(request.url)
        _logger.info(
            "Successfully fetched and stored HTML for URL: {} at {}".format(
                request.url, get_time_iso()
            )
        )

        document: ConvertedDocument = await handle_conversion(result)
        _logger.info(
            "Successfully converted document from URL: {} at {}".format(
                request.url, get_time_iso()
            )
        )

        return {
            "fetch_result": result.model_dump(),
            "converted_document": document.model_dump(),
            "markedown": document.markdown,
        }


    except Exception as e:
        _logger.error(
            "Error converting web document from URL {}: {} at {}".format(
                request.url, e, get_time_iso()
            ),
            exc_info=True,
            stack_info=True,
        )
        raise HTTPException(status_code=500, detail="Conversion Failed") from e



# endregion
