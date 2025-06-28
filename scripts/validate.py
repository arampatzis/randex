"""Script that validates a single question, or all questions inside a folder."""

import shutil
from datetime import datetime
from pathlib import Path

import click

from randex.exam import Exam, ExamTemplate, Pool, QuestionSet


@click.command(
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
def main(
    folder: Path,
    template_tex_path: Path,
    out_folder: Path,
    clean: bool,
    show_answers: bool,
    overwrite: bool,
) -> None:
    """
    Create a pdf file with all the questions defined in FOLDER.

    The FOLDER is traversed recursively.
    """
    if out_folder is None:
        out_folder = Path(f"tmp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    if out_folder.exists():
        if not overwrite:
            raise click.UsageError(
                f"Output folder '{out_folder}' already exists.\n"
                "Use --overwrite to remove it and continue.",
            )
        shutil.rmtree(out_folder)

    pool = Pool(folder=folder)

    pool.print_questions()
    questions_set = QuestionSet(questions=pool.questions)  # type: ignore[arg-type]
    number_of_questions = questions_set.size()
    questions = questions_set.sample(n=number_of_questions)
    exam_template = ExamTemplate.load(template_tex_path)

    exam = Exam(
        exam_template=exam_template,
        questions=questions,
        show_answers=show_answers,
    )
    exam.apply_shuffling(shuffle_questions=True, shuffle_answers=True)

    result = exam.compile(path=out_folder, clean=clean)

    print("STDOUT:")
    print("\n\t".join(result.stdout.splitlines()))
    print("STDERR:")
    print("\n\t".join(result.stderr.splitlines()))
