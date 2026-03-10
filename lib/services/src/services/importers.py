# region Docstring
"""
services.importers
Service for importing various file types and collections into the database.
Overview:
    - Provides a unified service for importing different file types (images, videos,
      audio, data, repositories, Obsidian vaults, web URLs) into the persistent storage layer.
    - Uses generator-based streaming responses to provide real-time status updates
      during long-running import operations.
    - Handles deduplication by checking existing records before inserting new ones.
"""

# endregion
# region Imports
import urllib.request
import mimetypes
from pathlib import Path
from logging import Logger as T_Logger
from typing import Generator

from sqlalchemy import func

from core.config import AppSettings
from core.database import DatabaseSessionGenerator as DBSession
from core.models import (
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
    AudioFile,
    AudioFileEntity,
    DataFile,
    DataFileEntity,
    WebFetchContent,
    WebFetchContentEntity,
)
from core.utils import ls_files, is_image_file, is_video_file, is_data_file
from .models import StreamingServiceResponse
from .scanning import RepoIndex


class FileImporterError(Exception):
    """Custom exception for file importer errors."""

    pass


def is_audio_file(path: Path) -> bool:
    mime, _ = mimetypes.guess_type(path.as_posix())
    return mime is not None and mime.startswith("audio/")


# endregion
# region File Importer Service
class ImageImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def scan_and_import(
        self, directory: Path
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Scanning directory %s for images...", directory)
        yield StreamingServiceResponse(
            status="Initiated", message=f"Scanning directory {directory} for images."
        )
        paths = ls_files(directory, logger=self.__logger)
        images = []
        for path in paths:
            if is_image_file(path):
                try:
                    images.append(ImageFile.populate(path))
                except Exception as e:
                    self.__logger.warning(
                        "Could not populate ImageFile for %s: %s", path, e
                    )
        yield StreamingServiceResponse(
            status="Processing", message=f"Found {len(images)} images to import."
        )
        yield from self.import_images(images)

    def import_images(
        self, images: list[ImageFile]
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Importing %s images...", str(len(images)))
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting import of {len(images)} images.",
        )
        try:
            with self.__db_session.get_session() as session:
                for image in images:
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

                    image_entity = image.entity
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


class VideoImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def scan_and_import(
        self, directory: Path
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Scanning directory %s for videos...", directory)
        yield StreamingServiceResponse(
            status="Initiated", message=f"Scanning directory {directory} for videos."
        )
        paths = ls_files(directory, logger=self.__logger)
        videos = []
        for path in paths:
            if is_video_file(path):
                try:
                    videos.append(VideoFile.populate(path))
                except Exception as e:
                    self.__logger.warning(
                        "Could not populate VideoFile for %s: %s", path, e
                    )
        yield StreamingServiceResponse(
            status="Processing", message=f"Found {len(videos)} videos to import."
        )
        yield from self.import_videos(videos)

    def import_videos(
        self, videos: list[VideoFile]
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info(f"Importing {len(videos)} videos...")
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting import of {len(videos)} videos.",
        )
        try:
            with self.__db_session.get_session() as session:
                for video in videos:
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

                    video_entity = video.entity
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


class AudioImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def scan_and_import(
        self, directory: Path
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Scanning directory %s for audio...", directory)
        yield StreamingServiceResponse(
            status="Initiated", message=f"Scanning directory {directory} for audio."
        )
        paths = ls_files(directory, logger=self.__logger)
        audios = []
        for path in paths:
            if is_audio_file(path):
                try:
                    audios.append(AudioFile.populate(path))
                except Exception as e:
                    self.__logger.warning(
                        "Could not populate AudioFile for %s: %s", path, e
                    )
        yield StreamingServiceResponse(
            status="Processing", message=f"Found {len(audios)} audio files to import."
        )
        yield from self.import_audios(audios)

    def import_audios(
        self, audios: list[AudioFile]
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info(f"Importing {len(audios)} audio files...")
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting import of {len(audios)} audio files.",
        )
        try:
            with self.__db_session.get_session() as session:
                for audio in audios:
                    existing_audio = session.get(AudioFileEntity, audio.id)
                    if existing_audio:
                        self.__logger.info(
                            "Audio with ID %s already exists. Skipping import.",
                            audio.id,
                        )
                        yield StreamingServiceResponse(
                            status="Conflict",
                            message=f"Audio with ID {audio.id} already exists.",
                        )
                        continue

                    audio_entity = audio.entity
                    session.add(audio_entity)
                    session.commit()
                    self.__logger.info(f"Imported audio with ID %s.", audio_entity.id)
                    yield StreamingServiceResponse(
                        status="Created",
                        message=f"Imported audio with ID {audio_entity.id}.",
                    )
        except Exception as e:
            self.__logger.exception("Failed to import audio. %s", str(e), exc_info=e)
            raise FileImporterError(f"Failed to import audio files: {str(e)}") from e


class DataImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def scan_and_import(
        self, directory: Path
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Scanning directory %s for data files...", directory)
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Scanning directory {directory} for data files.",
        )
        paths = ls_files(directory, logger=self.__logger)
        datas = []
        for path in paths:
            if is_data_file(path):
                try:
                    datas.append(DataFile.populate(path))
                except Exception as e:
                    self.__logger.warning(
                        "Could not populate DataFile for %s: %s", path, e
                    )
        yield StreamingServiceResponse(
            status="Processing", message=f"Found {len(datas)} data files to import."
        )
        yield from self.import_data_files(datas)

    def import_data_files(
        self, datas: list[DataFile]
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info(f"Importing {len(datas)} data files...")
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting import of {len(datas)} data files.",
        )
        try:
            with self.__db_session.get_session() as session:
                for data_file in datas:
                    existing_data = session.get(DataFileEntity, data_file.id)
                    if existing_data:
                        self.__logger.info(
                            "Data file with ID %s already exists. Skipping import.",
                            data_file.id,
                        )
                        yield StreamingServiceResponse(
                            status="Conflict",
                            message=f"Data file with ID {data_file.id} already exists.",
                        )
                        continue

                    data_entity = data_file.entity
                    session.add(data_entity)
                    session.commit()
                    self.__logger.info(
                        f"Imported data file with ID %s.", data_entity.id
                    )
                    yield StreamingServiceResponse(
                        status="Created",
                        message=f"Imported data file with ID {data_entity.id}.",
                    )
        except Exception as e:
            self.__logger.exception(
                "Failed to import data files. %s", str(e), exc_info=e
            )
            raise FileImporterError(f"Failed to import data files: {str(e)}") from e


class RepoImporterService:
    __db_session: DBSession
    __settings: AppSettings
    __logger: T_Logger

    def __init__(
        self, db_session: DBSession, settings: AppSettings, logger: T_Logger
    ) -> None:
        self.__db_session = db_session
        self.__settings = settings
        self.__logger = logger.getChild(self.__class__.__name__)

    def import_repository(
        self, path_or_url: str
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Starting repository import for: %s", path_or_url)
        yield StreamingServiceResponse(
            status="Initiated", message=f"Evaluating repository location: {path_or_url}"
        )

        try:
            is_url = (
                path_or_url.startswith("http://")
                or path_or_url.startswith("https://")
                or path_or_url.startswith("git@")
            )
            if is_url:
                repo_index = RepoIndex(logger=self.__logger, settings=self.__settings)
                target_path = repo_index.add_remote_repo(path_or_url)
                yield StreamingServiceResponse(
                    status="Processing", message=f"Cloned repository to {target_path}"
                )
            else:
                target_path = Path(path_or_url)

            repo_model = Repo.populate(target_path)
            yield StreamingServiceResponse(
                status="Processing",
                message=f"Populated repository model for {target_path.name}",
            )
            yield from self.import_repo(repo_model)
        except Exception as e:
            self.__logger.exception(
                "Failed to import repository %s. %s", path_or_url, str(e), exc_info=e
            )
            raise FileImporterError(f"Failed to import repository: {str(e)}") from e

    def import_repo(
        self, repo: Repo
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info(f"Importing repository '{repo.name}'...")
        yield StreamingServiceResponse(
            status="Initiated",
            message=f"Starting DB import of repository '{repo.name}'.",
        )
        try:
            with self.__db_session.get_session() as session:
                existing_repo = session.get(RepoEntity, repo.id)
                if existing_repo:
                    self.__logger.info(
                        "Repository with ID %s already exists. Updating files and metadata.",
                        repo.id,
                    )
                    existing_repo.git_metadata = repo.git_metadata
                    existing_repo.last_seen = func.now()
                    session.commit()
                    yield StreamingServiceResponse(
                        status="Updated",
                        message=f"Updated repository with ID {repo.id}.",
                    )
                else:
                    repo_entity = repo.entity
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

                    file_entity = file.entity
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


class ObsidianVaultImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def scan_and_import_vault(
        self, path: Path
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Scanning for Obsidian Vault at %s", path)
        yield StreamingServiceResponse(
            status="Initiated", message=f"Scanning for Obsidian Vault at {path}"
        )
        try:
            obsidian_dir = path / ".obsidian"
            if not obsidian_dir.exists() or not obsidian_dir.is_dir():
                yield StreamingServiceResponse(
                    status="Conflict",
                    message=f"No .obsidian directory found at {path}, skipping.",
                )
                return

            vault_model = ObsidianVault.populate(path)
            yield StreamingServiceResponse(
                status="Processing",
                message=f"Populated Obsidian Vault model for {vault_model.name}",
            )
            self.import_obsidian_vault(vault_model)
            yield StreamingServiceResponse(
                status="Created",
                message=f"Imported Obsidian Vault {vault_model.name} to DB successfully.",
            )
        except Exception as e:
            self.__logger.exception(
                "Failed to scan Obsidian Vault at %s: %s", path, str(e), exc_info=e
            )
            raise FileImporterError(f"Failed to scan Obsidian Vault: {str(e)}") from e

    def import_obsidian_vault(self, vault: ObsidianVault) -> None:
        self.__logger.info(f"Importing Obsidian vault '{vault.name}'...")
        try:
            with self.__db_session.get_session() as session:
                existing_vault = session.get(ObsidianVaultEntity, vault.id)
                if existing_vault:
                    self.__logger.info(
                        "Obsidian vault with ID %s already exists. Skipping import.",
                        vault.id,
                    )
                    return

                vault_entity = vault.entity
                session.add(vault_entity)
                session.commit()
                self.__logger.info(
                    f"Imported Obsidian vault with ID %s.", vault_entity.id
                )
                for note in vault.notes:
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
                    note_entity = note.entity
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


class WebImporterService:
    __db_session: DBSession
    __logger: T_Logger

    def __init__(self, db_session: DBSession, logger: T_Logger) -> None:
        self.__db_session = db_session
        self.__logger = logger.getChild(self.__class__.__name__)

    def fetch_and_import(
        self, url: str
    ) -> Generator[StreamingServiceResponse, None, None]:
        self.__logger.info("Fetching Web Content from %s", url)
        yield StreamingServiceResponse(
            status="Initiated", message=f"Fetching Web Content from {url}"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                html_bytes = response.read()
                html_content = html_bytes.decode("utf-8", errors="replace")

            uuid_val = str(hash(url))

            web_content = WebFetchContent(
                url=url, uuid=uuid_val, title="", summary="", tags=[]
            )
            web_entity = web_content.entity
            web_entity.bucket_path = ""  # Placeholder for S3 bucket path

            with self.__db_session.get_session() as session:
                existing = (
                    session.query(WebFetchContentEntity)
                    .filter_by(uuid=uuid_val)
                    .first()
                )
                if existing:
                    yield StreamingServiceResponse(
                        status="Conflict",
                        message=f"Web content for {url} already exists.",
                    )
                    return
                session.add(web_entity)
                session.commit()
                yield StreamingServiceResponse(
                    status="Created", message=f"Imported Web Content for {url}"
                )

        except Exception as e:
            self.__logger.exception(
                "Failed to fetch/import URL %s: %s", url, str(e), exc_info=e
            )
            raise FileImporterError(f"Failed to fetch/import URL: {str(e)}") from e


# endregion
