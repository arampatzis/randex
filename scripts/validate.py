from pathlib import Path
import yaml
import click
import subprocess

from randex.exam import Exam, Question

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
    help='Path to the yaml file that contains the header information',
)
@click.option(
    "--aux-path",
    "-a",
    type=Path,
    default='.',
    help='Run the latex compiler inside this folder',
)
def main(
    header_path: Path,
    question_path: Path,
    aux_path: Path,
) -> None:
    
    e = Exam()
    e.add_question(question_path)
    e.load_header(header_path)

    result = e.compile(aux_path)
    
    print("STDOUT:")
    print( "\n\t".join(result.stdout.splitlines()) )
    print("STDERR:")
    print( "\n\t".join(result.stderr.splitlines()) )
