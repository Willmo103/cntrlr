import typer
import logging
from pathlib import Path
from rich.console import Console
from core.config import get_settings, DatabaseSettings
from core.database import DatabaseSessionGenerator
from services.importers import (
    ImageImporterService,
    VideoImporterService,
    AudioImporterService,
    DataImporterService,
    ObsidianVaultImporterService,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("filetul")
console = Console()

ft = typer.Typer(
    name="filetul",
    help="A command-line tool to manage your files and directories.",
    add_completion=False,
)


def _get_db():
    db_settings = get_settings(DatabaseSettings)
    db_session = DatabaseSessionGenerator(db_settings)
    db_session.init_db()  # Ensure tables exist
    return db_session


def _print_status(status):
    if status.status == "Conflict":
        console.print(f"[yellow]{status.status}[/yellow]: {status.message}")
    elif status.status == "Created":
        console.print(f"[green]{status.status}[/green]: {status.message}")
    else:
        console.print(f"[cyan]{status.status}[/cyan]: {status.message}")


@ft.command()
def scan_images(directory: Path):
    """Scan and import images from a directory."""
    console.print(f"[bold blue]Scanning images in:[/bold blue] {directory}")
    db_session = _get_db()
    service = ImageImporterService(db_session, logger)
    for status in service.scan_and_import(directory):
        _print_status(status)


@ft.command()
def scan_videos(directory: Path):
    """Scan and import videos from a directory."""
    console.print(f"[bold blue]Scanning videos in:[/bold blue] {directory}")
    db_session = _get_db()
    service = VideoImporterService(db_session, logger)
    for status in service.scan_and_import(directory):
        _print_status(status)


@ft.command()
def scan_audio(directory: Path):
    """Scan and import audio from a directory."""
    console.print(f"[bold blue]Scanning audio in:[/bold blue] {directory}")
    db_session = _get_db()
    service = AudioImporterService(db_session, logger)
    for status in service.scan_and_import(directory):
        _print_status(status)


@ft.command()
def scan_data(directory: Path):
    """Scan and import data files from a directory."""
    console.print(f"[bold blue]Scanning data files in:[/bold blue] {directory}")
    db_session = _get_db()
    service = DataImporterService(db_session, logger)
    for status in service.scan_and_import(directory):
        _print_status(status)


@ft.command()
def scan_vault(directory: Path):
    """Scan and import an Obsidian Vault from a directory."""
    console.print(f"[bold blue]Scanning obsidian vault in:[/bold blue] {directory}")
    db_session = _get_db()
    service = ObsidianVaultImporterService(db_session, logger)
    for status in service.scan_and_import_vault(directory):
        _print_status(status)


def main():
    ft()
