import time

from fastapi import FastAPI

from routes import conversion_router, logger
from starlette.middleware.cors import CORSMiddleware

uptime_start = time.time()
api: FastAPI = None

try:
    api = FastAPI(
        title="Converter API",
        description="API for converting data with Docling",
        version="1.0.0",
    )
    cors = CORSMiddleware(
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.add_middleware(cors)
    api.include_router(conversion_router)
    logger.info("Converter API initialized.")

    @api.get("/")
    async def root() -> dict:
        return {
            "message": "Converter API is running.",
            "uptime_seconds": time.time() - uptime_start,
        }

    @api.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "uptime_seconds": time.time() - uptime_start}

except KeyboardInterrupt:
    logger.info("Shutting down Converter API due to keyboard interrupt.")
    raise

except Exception as e:
    logger.exception(
        f"Failed to initialize Converter API: {e}", exc_info=True, stack_info=True
    )
    raise e
