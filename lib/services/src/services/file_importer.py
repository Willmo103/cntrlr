from logging import Logger as T_Logger
from typing import Generator

from sqlalchemy import func

from core.database import DatabaseSessionGenerator as DBSession
from core.models import (  # noqa: F401
    ImageFile,
    ImageFileEntity,
    ObsidianNoteEntity,
    ObsidianVault,
    ObsidianVaultEntity,
    Repo,
    RepoEntity,
    RepoFileEntity,
    VideoFile,
    VideoFileEntity,
)

from .models import StreamingServiceResponse


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
    ) -> Generator[StreamingServiceResponse, None, None]:
        """
        Imports a list of image files into the system; yelds status messages.

        Arguments:
            images (list[ImageFile]): List of image files to import.

        Yeilds:
            StreamingServiceResponse: Status messages for each imported image.

        Raises:
            FileImporterError: If the import fails.

        Image files have a an `id` property that automatically generates a unique
        identifier upon creation. This `id` is used to track and reference the image
        so if an image with the same `id` already exists in the system, we can simply
        ignore it. for checking we should only be looking for the id to match.
        """
        self.__logger.info("Importing %s images...", str(len(images)))
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting import of {len(images)} images.",
        )
        try:
            with self.__db_session.get_session() as session:
                for image in images:
                    # Check if image already exists by ID
                    existing_image = session.get(ImageFileEntity, image.id)
                    if existing_image:
                        self.__logger.info(
                            "Image with ID %s already exists. Skipping import.",
                            image.id,
                        )
                        yield StreamingServiceResponse(
                            status="Conflict",
                            message=f"Image with ID {image.id} already exists.",
                        )
                        continue

                    # Create new ImageFileEntity from ImageFile model
                    image_entity = image.entity

                    # Add to session and commit
                    session.add(image_entity)
                    session.commit()
                    self.__logger.info(f"Imported image with ID %s.", image_entity.id)
                    yield StreamingServiceResponse(
                        status="Created",
                        message=f"Imported image with ID {image_entity.id}.",
                    )
        except Exception as e:
            self.__logger.exception("Failed to import images. %s", str(e), exc_info=e)
            raise FileImporterError(f"Failed to import images: {str(e)}") from e

    def import_videos(
        self, videos: list[VideoFile]
    ) -> Generator[StreamingServiceResponse, None, None]:
        """
        Imports a list of video files into the system; yelds status messages.

        Arguments:
            videos (list[VideoFile]): List of video files to import.

        Yeilds:
            StreamingServiceResponse: Status messages for each imported video.

        Raises:
            FileImporterError: If the import fails.
        """
        self.__logger.info(f"Importing {len(videos)} videos...")
        try:
            with self.__db_session.get_session() as session:
                for video in videos:
                    # Check if video already exists by ID
                    existing_video = session.get(VideoFileEntity, video.id)
                    if existing_video:
                        self.__logger.info(
                            "Video with ID %s already exists. Skipping import.",
                            video.id,
                        )
                        yield StreamingServiceResponse(
                            status="Conflict",
                            message=f"Video with ID {video.id} already exists.",
                        )
                        continue

                    # Create new VideoFileEntity from VideoFile model
                    video_entity = video.entity

                    # Add to session and commit
                    session.add(video_entity)
                    session.commit()
                    self.__logger.info(f"Imported video with ID %s.", video_entity.id)
                    yield StreamingServiceResponse(
                        status="Created",
                        message=f"Imported video with ID {video_entity.id}.",
                    )
        except Exception as e:
            self.__logger.exception("Failed to import videos. %s", str(e), exc_info=e)
            raise FileImporterError(f"Failed to import videos: {str(e)}") from e

    def import_repo(
        self, repo: Repo
    ) -> Generator[StreamingServiceResponse, None, None]:
        """
        Imports a code repository into the system; yelds status messages.

        Arguments:
            repo (Repo): The repository to import.

        Yeilds:
            StreamingServiceResponse: Status messages for the import process.
        Raises:
            FileImporterError: If the import fails.
        """
        self.__logger.info(f"Importing repository '{repo.name}'...")
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting import of repository '{repo.name}'.",
        )
        try:
            with self.__db_session.get_session() as session:
                # Check if repo already exists by ID
                existing_repo = session.get(RepoEntity, repo.id)
                if existing_repo:
                    self.__logger.info(
                        "Repository with ID %s already exists. Updating files and metadata.",
                        repo.id,
                    )
                    # update the existing repo metadata, last_seen timestamp, etc.
                    existing_repo.git_metadata = repo.git_metadata
                    existing_repo.last_seen = func.now()
                    session.commit()
                    yield StreamingServiceResponse(
                        status="Updated",
                        message=f"Updated repository with ID {repo.id}.",
                    )
                else:
                    # Create new RepoEntity from Repo model
                    repo_entity = repo.entity

                    # Add to session and commit
                    session.add(repo_entity)
                    session.commit()
                    self.__logger.info(
                        f"Imported repository with ID %s.", repo_entity.id
                    )
                    yield StreamingServiceResponse(
                        status="Created",
                        message=f"Imported repository with ID {repo_entity.id}.",
                    )
                for file in repo.files:
                    # Check if file exists in the repo by path
                    existing_file = (
                        session.query(RepoFileEntity)
                        .filter_by(repo_id=repo.id, id=file.id)
                        .first()
                    )
                    if existing_file:
                        self.__logger.info(
                            "File with ID %s already exists in repository %s. Skipping import.",
                            file.id,
                            repo.id,
                        )
                        yield StreamingServiceResponse(
                            status="Conflict",
                            message=f"No changes for file with ID {file.id} in repository {repo.id}.",
                        )
                        continue
                    # Create new RepoFileEntity from RepoFile model
                    file_entity = file.entity
                    # Add to session and commit
                    session.add(file_entity)
                    session.commit()
                    self.__logger.info(
                        f"Imported file with ID %s into repository %s.",
                        file_entity.id,
                        repo.id,
                    )
                    yield StreamingServiceResponse(
                        status="Created",
                        message=f"Imported file with ID {file_entity.id} into repository {repo.id}.",
                    )
        except Exception as e:
            self.__logger.exception(
                "Failed to import repository. %s", str(e), exc_info=e
            )
            raise FileImporterError(f"Failed to import repository: {str(e)}") from e

    def import_obsidian_vault(self, vault: ObsidianVault) -> None:
        """
        Imports an Obsidian vault into the system.

        Arguments:
            vault (ObsidianVault): The vault to import.

        Raises:
            FileImporterError: If the import fails.
        """
        self.__logger.info(f"Importing Obsidian vault '{vault.name}'...")
        try:
            with self.__db_session.get_session() as session:
                # Check if vault already exists by ID
                existing_vault = session.get(ObsidianVaultEntity, vault.id)
                if existing_vault:
                    self.__logger.info(
                        "Obsidian vault with ID %s already exists. Skipping import.",
                        vault.id,
                    )
                    return

                # Create new ObsidianVaultEntity from ObsidianVault model
                vault_entity = vault.entity

                # Add to session and commit
                session.add(vault_entity)
                session.commit()
                self.__logger.info(
                    f"Imported Obsidian vault with ID %s.", vault_entity.id
                )
                for note in vault.notes:
                    # Check if note exists in the vault by ID
                    existing_note = (
                        session.query(ObsidianNoteEntity)
                        .filter_by(vault_id=vault.id, id=note.id)
                        .first()
                    )
                    if existing_note:
                        self.__logger.info(
                            "Note with ID %s already exists in vault %s. Skipping import.",
                            note.id,
                            vault.id,
                        )
                        continue
                    # Create new ObsidianNoteEntity from ObsidianNote model
                    note_entity = note.entity
                    # Add to session and commit
                    session.add(note_entity)
                    session.commit()
                    self.__logger.info(
                        f"Imported note with ID %s into vault %s.",
                        note_entity.id,
                        vault.id,
                    )
        except Exception as e:
            self.__logger.exception(
                "Failed to import Obsidian vault. %s", str(e), exc_info=e
            )
            raise FileImporterError(f"Failed to import Obsidian vault: {str(e)}") from e


# endregion
