# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///
import sys
import typer # pyright: ignore[reportMissingImports]
import subprocess

from rich.console import Console  # pyright: ignore[reportMissingImports]
from rich.markdown import Markdown # pyright: ignore[reportMissingImports]

from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent.parent.resolve()

console = Console(
    record=True,
    width=120,
    color_system="auto",
)

app = typer.Typer(name="dev", help="Development CLI for CNTRLR application.")

def _ensure_venv():
    """Ensure that the virtual environment is activated."""
    if not hasattr(sys, 'real_prefix') and (getattr(sys, 'base_prefix', sys.prefix) == sys.prefix):
        console.print("[bold red]Error:[/bold red] Virtual environment is not activated.")
        console.print("Please activate the virtual environment before running this script.")
        typer.Exit(code=1)

def _activate_venv():
    """Activate the virtual environment."""
    venv_path = PACKAGE_ROOT / ".venv"
    if not venv_path.exists():
        raise EnvironmentError("Virtual environment not found. Please create it first.")
    activate_script = venv_path / "Scripts" / "activate_this.py" if sys.platform == "win32" else venv_path / "bin" / "activate_this.py"
    with open(activate_script) as f:
        exec(f.read(), {'__file__': str(activate_script)})

def _env_info_console_header() -> Console:
    console = Console()
    console.rule("[bold blue]CNTRLR Development Environment Info[/bold blue]")
    return console

@app.command(name="fmt", help="Format the codebase using black and isort.")
def format_code():
