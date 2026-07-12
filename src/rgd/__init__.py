from typing import Annotated
from pathlib import Path
import logging
import rich
from rich.logging import RichHandler


import typer


from .parser import loads, load
from .writer import dumps

__all__ = [
    "dump",
    "dumps",
    "loads",
    "load",
]


logging.basicConfig(format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logging.getLogger("rgd").setLevel(logging.WARNING)


app = typer.Typer()


@app.command("parse")
def parse_file(
    rgd_file: Path,
    verbose: Annotated[int, typer.Option("-v", count=True)] = 0
):
    logger = logging.getLogger("rgd")
    logger.setLevel(max((4 - verbose) * 10, 10))

    if not rgd_file.exists():
        raise FileNotFoundError(f"Could not find {rgd_file}")
    if not rgd_file.is_file():
        raise FileNotFoundError(f"File {rgd_file} is not a file!")
    if not rgd_file.suffix != "rgd":
        logger.warning(f"File extension {rgd_file.suffix} != 'rgd'")

    logger.info(f"Parsing {rgd_file}...")

    with open(rgd_file, 'r') as fp:
        graphs = load(fp)
    rich.print(graphs) 

    logger.info("Done!")



def main():
    app()

