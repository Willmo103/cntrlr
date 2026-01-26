# region Docstring
"""
...
"""
# endregion
# region Imports
from logging import Logger
from typing import Optional
from core.database import DatabaseSessionGenerator
from core.models.repo import RepoEntity, RepoScanResult, Repo
from pydantic import BaseModel

# endregion


# region Image Importer Service
# region Result Models
class RepoImporterResult(BaseModel):
    success: bool
    message: str
    url: str


# endregion
# region Service Classes
class RepoImporter:
    """
    Service for importing and processing repository scan results.
    """

    def __init__(self, db: DatabaseSessionGenerator, logger: Logger):
        """
        Initializes the RepoImporter with a database session generator and logger.

        Args:
            db (DatabaseSessionGenerator): The database session generator.
            logger (Logger): The logger instance for logging.
        """
        self.db_session_generator = db
        self.logger = logger.getChild("RepoImporter")

    def upsert_repo_and_files(self, scan_result: RepoScanResult) -> list[RepoImporterResult]:
        """
        Processes the repository scan result and imports repositories into the database.

        Args:
            scan_result (RepoScanResult): The result of the repository scan.

        Returns:
            list[RepoImporterResult]: A list of results for each imported repository.
        """
        repo: Optional[Repo] = scan_result.repo if scan_result.repo else None
        results: list[RepoImporterResult] = scan_result.results if scan_result.results else []

        with self.db_session_generator.get_session() as session:
