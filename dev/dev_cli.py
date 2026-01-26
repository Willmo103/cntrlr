# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///
import subprocess
from pathlib import Path

import typer  # pyright: ignore[reportMissingImports]
from rich.console import Console  # pyright: ignore[reportMissingImports]

PACKAGE_ROOT = Path(__file__).parent.parent.resolve()
LIBRARY_PATHS = {
    "core": PACKAGE_ROOT.parent / "lib" / "core",
    "services": PACKAGE_ROOT.parent / "lib" / "services",
}

console = Console(
    record=True,
    width=120,
    color_system="auto",
)

app = typer.Typer(name="dev", help="Development CLI for CNTRLR application.")


@app.command(name="fmt", help="Format the codebase using black and isort.")
def format_code():
    """Format the codebase using black and isort."""
    console.print("[bold green]Formatting code...[/bold green]")
    subprocess.run(
        ["uv", "run", "--active", "isort", str(PACKAGE_ROOT.as_posix())], check=True
    )
    console.print("[bold green]---[/bold green]")
    subprocess.run(
        ["uv", "run", "--active", "black", str(PACKAGE_ROOT.as_posix())], check=True
    )
    console.print("[bold green]Code formatting complete.[/bold green]")


if __name__ == "__main__":
    app()
