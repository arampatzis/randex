"""Grade the exams in the exams_path with the grades in the grades_path."""

import csv
import sys
from pathlib import Path

from randex.cli import get_logger
from randex.exam import ExamBatch

logger = get_logger(__name__)


def main(
    exams_path: Path, grades_path: Path, negative_score: float | None = None
) -> None:
    """
    Grade the exams in the exams_path with the grades in the grades_path.

    Parameters
    ----------
    exams_path : Path
        The path to the exams YAML file.
    grades_path : Path
        The path to the grades CSV file.
    negative_score : float | None
        The negative score for each wrong answer.
        If None, defaults to 1 / (number_of_answers - 1) per question.
    """
    logger.info("Grading exams from %s \nwith grades from %s", exams_path, grades_path)

    batch = ExamBatch.load(exams_path)

    if not batch.exams:
        logger.error("No exams found in the batch file: %s", exams_path)
        sys.exit(1)

    first_exam = next(iter(batch.exams.values()))
    num_questions = len(first_exam.questions)

    grades = []

    with open(grades_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            answers = [
                int(row[f"q{i + 1}"]) if row[f"q{i + 1}"] else None
                for i in range(num_questions)
            ]

            sn = int(row["sn"])
            if sn not in batch.exams:
                logger.warning("Exam with sn=%s not found in batch, skipping row.", sn)
                continue

            score = batch.exams[sn].grade(answers, negative_score)
            row["score"] = score
            grades += [row]

    with open(grades_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=grades[0].keys())
        writer.writeheader()
        for row in grades:
            writer.writerow(row)
