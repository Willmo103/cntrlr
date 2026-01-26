from logging import Logger as T_Logger
from typing import Generator

from core.database import DatabaseSessionGenerator as DBSession
from core.models import (  # Repo models; Obsidian models; Image/Video models
    ImageFile,
    ImageFileEntity,
    ObsidianNote,
    ObsidianNoteEntity,
    ObsidianVault,
    ObsidianVaultEntity,
    Repo,
    RepoEntity,
    RepoFile,
    RepoFileEntity,
    VideoFile,
    VideoFileEntity,
)


class FileImporterError(Exception):
    """Custom exception for file importer errors."""

    pass


# endregion
# region File Importer Service
class FileImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def import_images(
        self, images: list[ImageFile]
    ) -> Generator[dict[str, str], None, None]:
        """
        Imports a list of image files into the system; yelds status messages.

        Arguments:
            images (list[ImageFile]): List of image files to import.

        Yeilds:
            dict[str, str]: Status messages for each imported image.

        Raises:
            FileImporterError: If the import fails.

        Image files have a an `id` property that automatically generates a unique
        identifier upon creation. This `id` is used to track and reference the image
        so if an image with the same `id` already exists in the system, we can simply
        ignore it. for checking we should only be looking for the id to match.
        """
        self.__logger.info("Importing %s images...", str(len(images)))
        try:
            with self.__db_session.get_session as session:
                for image in images:
                    # Check if image already exists by ID
                    existing_image = session.get(ImageFileEntity, image.id)
                    if existing_image:
                        self.__logger.info(
                            "Image with ID %s already exists. Skipping import.",
                            image.id,
                        )
                        yield {
                            "status": "Conflict",
                            "message": f"Image with ID {image.id} already exists.",
                        }
                        continue

                    # Create new ImageFileEntity from ImageFile model
                    image_entity = image.entity

                    # Add to session and commit
                    session.add(image_entity)
                    session.commit()
                    self.__logger.info(f"Imported image with ID %s.", image_entity.id)
                    yield {
                        "status": "Created",
                        "message": f"Imported image with ID {image_entity.id}.",
                    }
        except Exception as e:
            self.__logger.exception("Failed to import images. %s", str(e), exc_info=e)
            raise FileImporterError(f"Failed to import images: {str(e)}") from e

    def import_videos(
        self, videos: list[VideoFile]
    ) -> Generator[dict[str, str], None, None]:
        """
        Imports a list of video files into the system; yelds status messages.

        Arguments:
            videos (list[VideoFile]): List of video files to import.

        Yeilds:
            dict[str, str]: Status messages for each imported video.

        Raises:
            FileImporterError: If the import fails.
        """
        self.__logger.info(f"Importing {len(videos)} videos...")
        ...

    def import_repo(self, repo: Repo) -> None:
        """
        Imports a Git repository into the system.

        Arguments:
            repo (Repo): The repository to import.

        Raises:
            FileImporterError: If the import fails.
        """
        self.__logger.info(f"Importing repo '{repo.name}'...")
        ...

    def import_obsidian_vault(self, vault: ObsidianVault) -> None:
        """
        Imports an Obsidian vault into the system.

        Arguments:
            vault (ObsidianVault): The vault to import.

        Raises:
            FileImporterError: If the import fails.
        """
        self.__logger.info(f"Importing Obsidian vault '{vault.name}'...")
        ...
