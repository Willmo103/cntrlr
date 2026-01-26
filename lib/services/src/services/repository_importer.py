# region Docstring
"""
...
"""
# endregion
# region Imports
from logging import Logger
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

    def __init__(self, db: DatabaseSessionGenerator):
        """
        Initializes the RepoImporter with a database session generator and logger.

        Args:
            db (DatabaseSessionGenerator): The database session generator.
            logger (Logger): The logger instance for logging.
        """
        self.db_session_generator = db

    def process_result(self, scan_result: RepoScanResult) -> list[RepoImporterResult]:
        """
        Processes the repository scan result and imports repositories into the database.

        Args:
            scan_result (RepoScanResult): The result of the repository scan.

        Returns:
            list[RepoImporterResult]: A list of results for each imported repository.
        """

        results = []
        with self.db_session_generator.get_session() as session:
            for repo in scan_result.repos:
                try:
                    repo_entity = RepoEntity(repo.model_dump())
                    session.add(repo_entity)
                    session.commit()
                    results.append(
                        RepoImporterResult(
                            success=True,
                            message=f"Imported repository: {repo.url}",
                            url=repo.url,
                        )
                    )
                except Exception as e:
                    self.logger.error(f"Failed to import repository {repo.url}: {e}")
                    results.append(
                        RepoImporterResult(
                            success=False,
                            message=f"Failed to import repository: {repo.url}. Error: {e}",
                            url=repo.url,
                        )
                    )
        return results
