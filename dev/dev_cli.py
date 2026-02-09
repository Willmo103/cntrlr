# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "sqlite-utils",
# ]
# ///
import subprocess
from pathlib import Path

import typer  # pyright: ignore[reportMissingImports]
from rich.console import Console  # pyright: ignore[reportMissingImports]
from sqlite_utils import Database

PACKAGE_ROOT = Path(__file__).parent.parent.resolve()
DEV_FOLDER = PACKAGE_ROOT / "dev"
DEV_DB: Database = Database(DEV_FOLDER / "dev.db")
LIBRARY_PATHS = {
    "core": PACKAGE_ROOT.parent / "lib" / "core",
    "services": PACKAGE_ROOT.parent / "lib" / "services",
    "converter": PACKAGE_ROOT.parent / "apps" / "converter",
}

console = Console(
    record=True,
    width=120,
    color_system="auto",
)

app = typer.Typer(name="dev", help="Development CLI for CNTRLR application.")


@app.command(name="fmt", help="Format the codebase using black and isort.")
def format_code():
    console.print("[bold green]Formatting code...[/bold green]")
    subprocess.run(
        ["uv", "run", "--active", "isort", str(PACKAGE_ROOT.as_posix())], check=True
    )
    console.print("[bold green]---[/bold green]")
    subprocess.run(
        ["uv", "run", "--active", "black", str(PACKAGE_ROOT.as_posix())], check=True
    )
    console.print("[bold green]Code formatting complete.[/bold green]")

@app.command(name="versions", help="Print the package versions for each library.")
def versions():
    console.print("[bold blue]Package Versions:[/bold blue]")
    for lib_name, lib_path in LIBRARY_PATHS.items():
        version_file = lib_path / "VERSION"
        if version_file.exists():
            version = version_file.read_text().strip()
            console.print(f"[bold cyan]{lib_name}:[/bold cyan] {version}")
        else:
            console.print(f"[bold red]{lib_name}:[/bold red] VERSION file not found.")


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise e
