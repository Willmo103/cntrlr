# region Docstrings
"""
"""
# endregion
# region Imports

from pathlib import Path
import httpx
from pydantic import BaseModel, Field
from docling.document_converter import DocumentConverter

from ..models import URLFetch
from ..logger import logger as _logger
from ..config import INPUT_STORAGE_PATH, CONVERTED_STORAGE_PATH
# from core.models.conversion_result import ConversionResultEntity, ConversionResult
from fastapi import APIRouter, HTTPException, Request
from core.utils import get_time_iso

# endregion
# region API Models


class URLConversionRequest(BaseModel):
    url: str = Field(..., description="The URL of the document to be converted.")


# endregion
# region API Router and Endpoints

conversion_api = APIRouter(prefix="/api", tags=["conversion"])
_html_storage_path_ = INPUT_STORAGE_PATH / "html"
_input_document_storage_path_ = INPUT_STORAGE_PATH / "uploaded"
_converted_storage_path_ = CONVERTED_STORAGE_PATH / "dl_documents"
_converted_storage_path_.mkdir(parents=True, exist_ok=True)
_html_storage_path_.mkdir(parents=True, exist_ok=True)
_input_document_storage_path_.mkdir(parents=True, exist_ok=True)

async def handle_fetch_request(url: str) -> str:
    """Fetch the content of the URL and store it locally."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text

            # Store content to a local file (for demonstration, using URL hash as filename)
            filename = Path(f"stored_contents/{hash(url)}.html")
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)


            return str(filename)
    except httpx.HTTPError as e:
        _logger.error(f"Failed to fetch URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}") from e

async def handle_file_upload(request: Request) -> Path:
    """Handle file upload and store it locally."""
    try:
        form = await request.form()
        upload_file = form.get("file")
        if not upload_file:
            raise HTTPException(status_code=400, detail="No file uploaded.")
        file_location = _input_document_storage_path_ / upload_file.filename
        with open(file_location, "wb") as f:
            f.write(await upload_file.read())
        return file_location
    except Exception as e:
        _logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.") from e

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
