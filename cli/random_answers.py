"""Generate random answers for the exams in the exams_path."""

import csv
import random
from pathlib import Path
from typing import cast

from randex.cli import get_logger
from randex.exam import ExamBatch

logger = get_logger(__name__)


def main(exams_path: Path) -> None:
    """
    Generate random answers for the exams in the exams_path.

    Parameters
    ----------
    exams_path : Path
        The path to the exams YAML file.
    """
    batch = ExamBatch.load(exams_path)

    # Generate random answers for each exam
    all_answers: dict[int, list[int | None]] = {}
    for exam in batch.exams.values():
        sn = int(exam.sn)
        match sn:
            case 0:
                all_answers[sn] = cast("list[int | None]", exam.right_answers)
            case 1:
                num_questions = len(exam.questions)
                num_none = random.randint(1, num_questions)

                indices_to_none = random.sample(range(num_questions), num_none)
                all_answers[sn] = [
                    None
                    if i in indices_to_none
                    else random.randint(0, len(question.answers) - 1)
                    for i, question in enumerate(exam.questions)
                ]
            case 2:
                all_answers[sn] = [None] * len(exam.questions)
            case _:
                all_answers[sn] = [
                    random.randint(0, len(question.answers) - 1)
                    for question in exam.questions
                ]

    answers = dict(sorted(all_answers.items()))
    fieldnames = ["sn"] + [f"q{i + 1}" for i in range(len(batch.exams[0].questions))]

    # Save the answers to a CSV file
    save_path = exams_path.parent / "random_answers.csv"
    with open(save_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sn, values in answers.items():
            row: dict[str, int | str] = {"sn": sn}
            row.update(
                {f"q{i + 1}": v if v is not None else "" for i, v in enumerate(values)}
            )
            writer.writerow(row)

    logger.info("✅ Random answers saved to %s", save_path)
