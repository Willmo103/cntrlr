import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .logger import api_settings, logger
from .routes.api import conversion_api
from .routes.ui import ui_router

uptime_start = time.time()
app: FastAPI = None

try:
    app = FastAPI(
        title="Converter API",
        description="API for converting data with Docling",
        version="1.0.0",
    )
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(conversion_api)
    app.include_router(ui_router)
    logger.info("Converter API initialized.")

    @app.get("/")
    async def root() -> dict:
        return {
            "message": "Converter API is running.",
            "uptime_seconds": time.time() - uptime_start,
        }

    @app.get("/health")
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


def entry():
    """Entry point for running the Converter application."""
    import uvicorn

    uvicorn.run(
        "converter.main:app",
        host=api_settings.host,
        port=api_settings.port,
        log_level=api_settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    entry()
