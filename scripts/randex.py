"""Main CLI for randex - Create randomized multiple choice exams using latex."""

import importlib.metadata
from pathlib import Path

import click

from randex.cli import CustomCommand, setup_logging
from scripts.batch import main as batch_main
from scripts.download_examples import main as download_examples_main
from scripts.validate import main as validate_main

try:
    __version__ = importlib.metadata.version("randex")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


# Main CLI group
@click.group()
@click.version_option(version=__version__, prog_name="randex")
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (use -v for DEBUG, -vv for more detailed DEBUG output)",
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Quiet mode - only show warnings and errors"
)
@click.pass_context
def cli(ctx: click.Context, verbose: int, quiet: bool) -> None:
    """randex: A CLI tool to create randomized multiple choice exams using latex."""
    # Set up logging before any command runs
    setup_logging(verbose=verbose, quiet=quiet)

    # Store logging config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


# Subcommand: download-examples # noqa: ERA001
@cli.command(
    cls=CustomCommand,
    context_settings={"help_option_names": ["--help"]},
)
def download_examples() -> None:
    """Download the latest examples from GitHub."""
    download_examples_main()


@cli.command(
    cls=CustomCommand,
    context_settings={"help_option_names": ["--help"]},
)
@click.argument(
    "folder",
    type=str,
    nargs=1,
    required=True,
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=1,
    help="Number of exams to be created",
)
@click.option(
    "--number_of_questions",
    "-n",
    type=int,
    default=[1],
    multiple=True,
    help="""
    Specify how many questions to sample.

    - Use once: sample total number of questions from all folders.
    Example: -n 10

    - Use multiple times: sample per-folder counts, in order.
    Example: -n 5 -n 3   # 5 from folder 1, 3 from folder 2
    """,
)
@click.option(
    "--template-tex-path",
    "-t",
    type=click.Path(
        exists=True,
        resolve_path=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
    ),
    required=True,
    help="Path to the YAML file that contains the template for the exam configuration",
)
@click.option(
    "--out-folder",
    "-o",
    type=Path,
    help="Create the batch exams in this folder (default: tmp_HH-MM-SS)",
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    default=False,
    help="Clean all latex compilation auxiliary files",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the out-folder if it already exists (use with caution).",
)
@click.option(
    "--sequential",
    is_flag=True,
    default=False,
    help="Use sequential compilation instead of parallel.",
)
def batch(
    folder: str,
    batch_size: int,
    number_of_questions: list | int,
    template_tex_path: Path,
    out_folder: Path | None,
    clean: bool,
    overwrite: bool,
    sequential: bool,
) -> None:
    """
    Create a batch of exams with randomly chosen multiple choice questions.

    The questions are loaded from a list of FOLDERS.

    FOLDER: Path or quoted glob (e.g. "data/unit_*").

    The questions are loaded from the FOLDERs and must follow the format:

    question: What is $1+1$?
    answers: ["0", "1", "2", "3"]
    right_answer: 2

    💡 Remember to wrap glob patterns in quotes to prevent shell expansion!

    """
    batch_main(
        folder=folder,
        batch_size=batch_size,
        number_of_questions=number_of_questions,
        template_tex_path=template_tex_path,
        out_folder=out_folder,
        clean=clean,
        overwrite=overwrite,
        sequential=sequential,
    )


@cli.command(
    cls=CustomCommand,
    context_settings={"help_option_names": ["--help"]},
)
@click.argument(
    "folder",
    type=str,
    nargs=1,
    required=True,
)
@click.option(
    "--template-tex-path",
    "-t",
    type=click.Path(
        exists=True,
        resolve_path=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
    ),
    required=True,
    help="Path to the YAML file that contains the template for the exam configuration",
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
    "--show-answers",
    "-a",
    is_flag=True,
    default=False,
    help="Show the right answers on the pdf",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the out-folder if it already exists (use with caution).",
)
def validate(
    folder: str,
    template_tex_path: Path,
    out_folder: Path,
    clean: bool,
    show_answers: bool,
    overwrite: bool,
) -> None:
    """
    Create a pdf file with all the questions defined in FOLDER.

    The FOLDER is traversed recursively to load all questions.
    """
    validate_main(
        folder=folder,
        template_tex_path=template_tex_path,
        out_folder=out_folder,
        clean=clean,
        show_answers=show_answers,
        overwrite=overwrite,
    )


if __name__ == "__main__":
    cli()
