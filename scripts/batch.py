"""Script that creates a batch of randomized exams."""

import shutil
import sys
from datetime import datetime
from pathlib import Path

import click
from pydantic import ValidationError

from randex.cli import get_logger
from randex.exam import ExamBatch, ExamTemplate, Pool, QuestionSet

logger = get_logger(__name__)


def main(
    *,
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

    Parameters
    ----------
    folder : str
        Path or quoted glob (e.g. "examples/en/folder_*").
    number_of_questions : list | int
        Number of questions to sample.
    batch_size : int
        Number of exams to be created.
    template_tex_path : Path
        Path to the YAML file that contains the template for the exam configuration.
    out_folder : Path | None
        Create the batch exams in this folder (default: tmp_HH-MM-SS).
    clean : bool
        Clean the output folder before creating the exams.
    overwrite : bool
        Overwrite the output folder if it already exists.
    """
    if out_folder is None:
        out_folder = Path(f"tmp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    logger.info("📁 Output folder: %s", out_folder)

    if out_folder.exists():
        if not overwrite:
            raise click.UsageError(
                f"Output folder '{out_folder}' already exists.\n"
                "Use --overwrite to remove it and continue.",
            )
        logger.warning("🗑️  Removing existing output folder: %s", out_folder)
        shutil.rmtree(out_folder)

    if isinstance(number_of_questions, list | tuple) and len(number_of_questions) == 1:
        number_of_questions = number_of_questions[0]

    logger.info("📂 Loading questions from: %s", folder)
    pool = Pool(folder=folder)

    pool.print_questions()
    questions_set = QuestionSet(questions=pool.questions)  # type: ignore[arg-type]
    questions_set.sample(n=number_of_questions)

    logger.info("📄 Loading exam template from: %s", template_tex_path)
    exam_template = ExamTemplate.load(template_tex_path)

    try:
        logger.info("🔄 Creating batch of %d exams...", batch_size)
        b = ExamBatch(
            N=batch_size,
            questions_set=questions_set,
            exam_template=exam_template,
            n=number_of_questions,
        )
    except ValidationError as e:
        logger.exception("❌ Validation error while creating exam batch:")
        logger.exception(e.json(indent=2))
        sys.exit(1)

    b.make_batch()

    logger.info("🔨 Compiling exams...")
    b.compile(clean=clean, path=out_folder)

    logger.info("💾 Saving batch configuration to: %s", out_folder / "exams.yaml")
    b.save(out_folder / "exams.yaml")

    logger.debug("🔄 Reloading and recompiling batch...")
    b = ExamBatch.load(out_folder / "exams.yaml")
    b.compile(clean=clean, path=out_folder)

    logger.info("✅ Batch creation completed successfully in: %s", out_folder)
