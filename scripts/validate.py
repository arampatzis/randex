"""Script that validates a single question, or all questions inside a folder."""
from pathlib import Path
from dataclasses import asdict

import click

from randex.exam import Exam, Header
from randex.schema import validate

@click.command(
    context_settings={"help_option_names": ["--help"]},
)
@click.argument(
    "question_path",
    type=Path,
)
@click.option(
    "--header-path",
    "-h",
    type=Path,
    help="Path to the yaml file that contains the header information",
)
@click.option(
    "--aux-path",
    "-a",
    type=Path,
    default=".",
    help="Run the latex compiler inside this folder",
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    default=False,
    help="Clean all latex compilation auxiliary files.",
)
def main(
    header_path: Path,
    question_path: Path,
    aux_path: Path,
    clean: bool,
) -> None:
    """Run the main tasks of the script."""
    
    header = Header.load(header_path)
    
    e = Exam(header=header)
    e.add_question(question_path)

    result = e.compile(aux_path, clean=clean)

    print("STDOUT:")
    print("\n\t".join(result.stdout.splitlines()))
    print("STDERR:")
    print("\n\t".join(result.stderr.splitlines()))
