"""Script that validates a single question, or all questions inside a folder."""
from pathlib import Path

import click

from randex.exam import Exam, Tex


@click.command(
    context_settings={"help_option_names": ["--help"]},
)
@click.argument(
    "question_path",
    type=Path,
)
@click.option(
    "--tex-path",
    "-t",
    type=Path,
    help="Path to the yaml file that contains the exam configuration",
)
@click.option(
    "--out-folder",
    "-o",
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
@click.option(
    "--answers",
    "-a",
    is_flag=True,
    default=False,
    help="Show the right answers on the pdf.",
)
def main(
    tex_path: Path,
    question_path: Path,
    out_folder: Path,
    clean: bool,
    answers: bool,
) -> None:
    """Run the main tasks of the script."""
    header = Tex.load(tex_path)

    e = Exam(tex=header, show_answers=answers)

    e.add_question(question_path)

    result = e.compile(out_folder, clean=clean)

    print("STDOUT:")
    print("\n\t".join(result.stdout.splitlines()))
    print("STDERR:")
    print("\n\t".join(result.stderr.splitlines()))
