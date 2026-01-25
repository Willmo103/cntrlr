# region Imports
from logging import Logger
from core.config import DatabaseSettings
from core.database import DatabaseSessionGenerator
from core.models.file_system.image_file import ImageFile, ImageFileEntity, ImageScanResult

# endregion
# region Image Importer Service
class ImageImporter:
    """
    Service for importing and processing image files.
    """

    def __init__(self, db_settings: DatabaseSettings, logger: Logger):
        self.db_session_generator = DatabaseSessionGenerator(db_settings)
        self.logger = logger

    def
