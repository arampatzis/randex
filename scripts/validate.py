"""Script that validates a single question, or all questions inside a folder."""

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import click

from randex.cli import get_logger
from randex.exam import Exam, ExamTemplate, Pool, QuestionSet

logger = get_logger(__name__)


def _setup_output_folder(out_folder: Path | str | None, overwrite: bool) -> Path:
    """
    Set up the output folder for validation.

    Parameters
    ----------
    out_folder : Path | None
        The output folder path, or None to generate a default.
    overwrite : bool
        Whether to overwrite existing folders.

    Returns
    -------
    Path
        The prepared output folder path.
    """
    if out_folder is None:
        out_folder = Path(f"tmp_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    out_folder = Path(out_folder)

    logger.info("📁 Output folder: %s", out_folder)

    if out_folder.exists():
        if not overwrite:
            raise click.UsageError(
                f"Output folder '{out_folder}' already exists.\n"
                "Use --overwrite to remove it and continue.",
            )
        logger.warning("🗑️  Removing existing output folder: %s", out_folder)
        shutil.rmtree(out_folder)

    return out_folder


def _handle_compilation_result(
    result: subprocess.CompletedProcess,
    out_folder: Path | str,
) -> None:
    """
    Handle and log the compilation results.

    Parameters
    ----------
    result : subprocess.CompletedProcess
        The compilation result from LaTeX.
    out_folder : Path
        The output folder path for success messages.
    """
    if result.stdout:
        logger.debug("LaTeX compilation STDOUT:")
        for line in result.stdout.splitlines():
            logger.debug("  %s", line)

    if result.stderr:
        if result.returncode != 0:
            logger.error("LaTeX compilation STDERR:")
            for line in result.stderr.splitlines():
                logger.error("  %s", line)
        else:
            logger.debug("LaTeX compilation STDERR:")
            for line in result.stderr.splitlines():
                logger.debug("  %s", line)

    if result.returncode == 0:
        logger.info("✅ Validation completed successfully in: %s", out_folder)
    else:
        logger.error(
            "❌ LaTeX compilation failed with return code: %d", result.returncode
        )


def main(
    *,
    folder: Path | str,
    template_tex_path: Path | str,
    out_folder: Path | str | None,
    clean: bool,
    show_answers: bool,
    overwrite: bool,
) -> None:
    """
    Create a pdf file with all the questions defined in FOLDER.

    The FOLDER is traversed recursively.
    """
    out_folder = _setup_output_folder(out_folder, overwrite)

    logger.info("📂 Loading questions from: %s", folder)
    pool = Pool(folder=folder)

    if logger.isEnabledFor(logging.DEBUG):
        pool.print_questions()

    questions_set = QuestionSet(questions=pool.questions)  # type: ignore[arg-type]
    number_of_questions = questions_set.size()
    questions = questions_set.sample(n=number_of_questions)

    logger.info("📄 Loading exam template from: %s", template_tex_path)
    exam_template = ExamTemplate.load(Path(template_tex_path))

    logger.info("📝 Creating validation exam with %d questions", number_of_questions)
    exam = Exam(
        exam_template=exam_template,
        questions=questions,
        show_answers=show_answers,
    )
    exam.apply_shuffling(shuffle_questions=True, shuffle_answers=True)

    logger.info("🔨 Compiling exam...")
    result = exam.compile(path=out_folder, clean=clean)

    _handle_compilation_result(result, out_folder)
