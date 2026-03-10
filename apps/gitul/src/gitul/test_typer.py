import typer

gt = typer.Typer()


@gt.command()
def import_repo(url_or_path: str):
    print(f"Importing {url_or_path}")


def main():
    gt()
