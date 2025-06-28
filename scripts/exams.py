"""Script that creates a batch of randomized exams."""

import shutil
from datetime import datetime
from pathlib import Path

import click

from randex.exam import ExamBatch, ExamTemplate, Pool, QuestionSet


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
def main(
    folder: str,
    number_of_questions: list | int,
    batch_size: int,
    template_tex_path: Path,
    out_folder: Path | None,
    clean: bool,
    overwrite: bool,
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
    if out_folder is None:
        out_folder = Path(f"tmp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    if out_folder.exists():
        if not overwrite:
            raise click.UsageError(
                f"Output folder '{out_folder}' already exists.\n"
                "Use --overwrite to remove it and continue.",
            )
        shutil.rmtree(out_folder)

    if isinstance(number_of_questions, list | tuple) and len(number_of_questions) == 1:
        number_of_questions = number_of_questions[0]

    pool = Pool(folder=folder)

    pool.print_questions()
    questions_set = QuestionSet(questions=pool.questions)  # type: ignore[arg-type]
    questions_set.sample(n=number_of_questions)
    exam_template = ExamTemplate.load(template_tex_path)

    b = ExamBatch(
        N=batch_size,
        questions_set=questions_set,
        exam_template=exam_template,
        n=number_of_questions,
    )

    b.make_batch()

    b.compile(clean=clean, path=out_folder)

    b.save(out_folder / "exams.yaml")

    b = ExamBatch.load(out_folder / "exams.yaml")

    b.compile(clean=clean, path=out_folder)
