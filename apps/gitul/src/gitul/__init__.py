import typer
import logging
from rich.console import Console
from core.config import get_settings, AppSettings, DatabaseSettings
from core.database import DatabaseSessionGenerator
from services.importers import RepoImporterService

# Setup minimal logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("gitul")
console = Console()

gt = typer.Typer(
    name="gitul",
    help="A command-line tool to manage your Git repositories.",
    add_completion=False,
)


@gt.command()
def import_repo(url_or_path: str):
    """Import a repository from a remote URL or local path into the database."""
    console.print(f"[bold blue]Starting import for:[/bold blue] {url_or_path}")

    db_settings = get_settings(DatabaseSettings)
    app_settings = get_settings(AppSettings)

    db_session = DatabaseSessionGenerator(db_settings)
    db_session.init_db()  # Ensure tables exist

    service = RepoImporterService(
        db_session=db_session, settings=app_settings, logger=logger
    )

    for status in service.import_repository(url_or_path):
        if status.status == "Conflict":
            console.print(f"[yellow]{status.status}[/yellow]: {status.message}")
        elif status.status == "Created":
            console.print(f"[green]{status.status}[/green]: {status.message}")
        else:
            console.print(f"[cyan]{status.status}[/cyan]: {status.message}")

    console.print("[bold green]Import complete![/bold green]")


def main():
    gt()
