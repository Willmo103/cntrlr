from ..logger import logger as _logger

# from core.models.conversion_result import ConversionResultEntity, ConversionResult
from fastapi import APIRouter, HTTPException, Request
from core.utils import get_time_iso

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
