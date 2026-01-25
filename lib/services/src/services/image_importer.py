# region Docstring
"""
services.image_importer
Service module for importing and processing image files into the database.
Overview:
- Provides a service class for batch importing image files from scan results
    into a persistent database storage.
- Handles database session management, error handling, and transaction rollback
    for failed imports.
- Returns detailed import results for each processed image file.
Contents:
- Result Models:
    - ImporterResult:
        A Pydantic model representing the outcome of a single image import operation.
        Contains success status (bool) and a descriptive message (str).
- Service Classes:
    - ImageImporter:
        Main service class for importing image files. Accepts a database session
        generator and logger at initialization. Processes ImageScanResult objects
        and persists ImageFileEntity records to the database with transaction
        management and error logging.
Design Notes:
- Uses context manager pattern for database session handling to ensure proper
    cleanup and connection management.
- Each image file import is handled individually with commit/rollback semantics
    to prevent partial batch failures from affecting successfully imported files.
- Logging is namespaced under the parent logger with "ImageImporter" child logger
    for traceable error reporting.
- Compatible with ImageScanResult from core.models.file_system.image_file which
    extends BaseScanResult patterns.

"""
# endregion
# region Imports
from logging import Logger
from core.database import DatabaseSessionGenerator
from core.models.file_system.image_file import (
    ImageFileEntity,
    ImageScanResult,
)
from pydantic import BaseModel


# endregion
# region Image Importer Service
# region Result Models
class ImporterResult(BaseModel):
    success: bool
    message: str


# endregion
# region Service Classes
class ImageImporter:
    """
    Service for importing and processing image files.
    """

    def __init__(self, db: DatabaseSessionGenerator, logger: Logger):
        """
        Initializes the ImageImporter with a database session generator and logger.

        Args:
            db (DatabaseSessionGenerator): The database session generator.
            logger (Logger): The logger instance for logging.
        """
        self.db_session_generator = db
        self.logger = logger.getChild("ImageImporter")

    def process_result(self, scan_result: ImageScanResult) -> list[ImporterResult]:
        """
        Processes the image scan result and imports image files into the database.

        Args:
            scan_result (ImageScanResult): The result of the image scan.

        Returns:
            list[ImporterResult]: A list of results for each imported image file.
        """
        results = []
        with self.db_session_generator.get_session() as session:
            for image_file in scan_result.files:
                try:
                    image_entity = ImageFileEntity(image_file.model_dump())
                    session.add(image_entity)
                    session.commit()
                    results.append(
                        ImporterResult(
                            success=True,
                            message=f"Imported image file: {image_file.Path.as_posix()}",
                        )
                    )
                except Exception as e:
                    session.rollback()
                    self.logger.error(
                        f"Failed to import image file {image_file.Path.as_posix()}: {e}"
                    )
                    results.append(
                        ImporterResult(
                            success=False,
                            message=f"Failed to import image file: {image_file.Path.as_posix()}",
                        )
                    )
        return results


# endregion
__all__ = ["ImageImporter", "ImporterResult"]
