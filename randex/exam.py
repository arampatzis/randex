"""
Implementation of the Question and the Exam classes.

These classes are the building block of the library.
"""

from __future__ import annotations

import logging
import subprocess
import time
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from random import sample, shuffle

import yaml
from pydantic import BaseModel, field_validator, model_validator
from pypdf import PdfWriter
from typing_extensions import Self

logger = logging.getLogger(__name__)


def is_glob_expression(s: str) -> bool:
    """
    Check if a string is a glob expression.

    Parameters
    ----------
    s : str
        The string to check.

    Returns
    -------
    bool:
        True if the string is a glob expression, False otherwise.
    """
    return any(char in s for char in "*?[]")


class Question(BaseModel):
    """
    Represents a multiple-choice question with a correct answer.

    Provides methods for LaTeX export and answer shuffling.

    Attributes
    ----------
    question : str
        The question text.
    answers : list[str]
        The list of answers.
    right_answer : int
        The index of the correct answer.
    """

    question: str
    answers: list[str]
    right_answer: int

    @field_validator("answers", mode="before")
    @classmethod
    def validate_answers(cls, v: list[str]) -> list[str]:
        """
        Validate the answers field.

        Parameters
        ----------
        v : list
            The answers to validate.

        Returns
        -------
        list[str]:
            A list of strings.
        """
        if not isinstance(v, list):
            raise TypeError("'answers' must be a list")
        return [str(a) for a in v]

    @field_validator("right_answer", mode="before")
    @classmethod
    def validate_right_answer_type(cls, v: int) -> int:
        """
        Validate the type of the right_answer field.

        Parameters
        ----------
        v : int
            The right answer to validate.

        Returns
        -------
        int:
            The right answer.
        """
        try:
            return int(v)
        except ValueError as e:
            raise TypeError("'right_answer' must be coercible to an integer") from e

    @model_validator(mode="after")
    def validate_right_answer_value(self) -> Question:
        """
        Validate the value of the right answer.

        Returns
        -------
        Question:
            The Question object.
        """
        if not (0 <= self.right_answer < len(self.answers)):
            raise IndexError(
                f"'right_answer' index {self.right_answer} is out of bounds"
            )
        return self

    def shuffle(self) -> Question:
        """
        Shuffle the answers of the question.

        Returns
        -------
        Question:
            A new Question object with shuffled answers.
        """
        new_q = deepcopy(self)
        correct = new_q.answers[new_q.right_answer]
        shuffled = new_q.answers[:]
        shuffle(shuffled)
        new_q.answers = shuffled
        new_q.right_answer = shuffled.index(correct)
        return new_q

    def to_latex(self) -> str:
        """
        Return LaTeX code for the question set with shuffled answers.

        Returns
        -------
        str:
            A string containing the LaTeX code for the question set
            with shuffled answers.
        """
        lines = [f"\\question {self.question}", "\\begin{oneparchoices}"]
        for i, ans in enumerate(self.answers):
            prefix = "\\correctchoice" if i == self.right_answer else "\\choice"
            lines.append(f"    {prefix} {ans}")
        lines.append("\\end{oneparchoices}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """
        Return a string representation of the question.

        Returns
        -------
        str:
            A string representation of the question.
        """
        lines = [f"Q: {self.question}"]
        for i, ans in enumerate(self.answers):
            mark = "✓" if i == self.right_answer else " "
            lines.append(f"  [{mark}] {i}. {ans}")
        return "\n".join(lines)


@dataclass(frozen=True, kw_only=True)
class Pool:
    """
    Represents a pool of validated YAML questions.

    Input:
    - If `folder` is a glob string: matched folders are used directly.
    - If `folder` is a path: that folder and its one-level subfolders are used.

    Questions are loaded non-recursively from each folder, and must follow the format:

    question: What is $1+1$?
    answers: ["0", "1", "2", "3"]
    right_answer: 2
    points: 1
    """

    folder: str | Path

    def resolve_folder_input(self) -> list[Path]:
        """
        Resolve the folder input to a list of directories (glob or path + subdirs).

        Returns
        -------
        list[Path]:
            A list of directories.
        """
        folder_input = self.folder

        if isinstance(folder_input, str) and is_glob_expression(folder_input):
            matched = [p.resolve() for p in Path().glob(folder_input) if p.is_dir()]
            if not matched:
                raise ValueError(
                    f"❌ No folders found matching the pattern: '{folder_input}'\n\n"
                    f"💡 Suggestions:\n"
                    f"   • Check if the path exists and contains folders\n"
                    f"   • Verify the spelling (common mistake: 'example' vs 'examples')\n"  # noqa: E501
                    f"   • Use quotes around the pattern to prevent shell expansion\n"
                    f"   • Try listing the directory to see available folders\n\n"
                    f"🔍 If '{folder_input}' is meant to be a literal folder name (not a pattern), "  # noqa: E501
                    f"remove the special characters or use a Path object instead."
                )
            return matched

        folder = Path(folder_input).resolve()
        if not folder.is_dir():
            raise NotADirectoryError(f"{folder} is not a directory")

        return [folder] + [f for f in folder.iterdir() if f.is_dir()]

    @cached_property
    def questions(self) -> OrderedDict[Path, list[Question]]:
        """
        Maps: folder → list of validated questions.

        Only includes folders with valid questions, sorted by name.

        Returns
        -------
        OrderedDict[Path, list[Question]]:
            A dictionary mapping folders to lists of questions.
        """
        result = {}

        for folder in self.resolve_folder_input():
            folder_questions = []

            for f in folder.iterdir():
                if not f.is_file() or f.suffix.lower() not in {".yaml", ".yml"}:
                    continue

                try:
                    with f.open("r", encoding="utf-8") as stream:
                        data = yaml.safe_load(stream)
                        question = Question(**data)
                        folder_questions.append(question)
                except (yaml.YAMLError, TypeError, ValueError) as e:
                    logger.warning("Skipping %s (invalid question): %s", f, e)
            if folder_questions:
                result[folder] = folder_questions
                logger.debug(
                    "Found %s valid questions in %s",
                    len(folder_questions),
                    folder,
                )
            else:
                logger.info("No valid questions found in %s, excluding it.", folder)

        return OrderedDict(sorted(result.items(), key=lambda x: x[0].name))

    @cached_property
    def folders(self) -> tuple[Path, ...]:
        """
        Return folders containing at least one valid question, sorted by name.

        Returns
        -------
        tuple[Path, ...]:
            A tuple of folders.
        """
        return tuple(self.questions.keys())

    @cached_property
    def number_of_folders(self) -> int:
        """
        Return the total number of folders.

        Returns
        -------
        int:
            The number of folders.
        """
        return len(self.questions)

    def __str__(self) -> str:
        """
        Return a string representation of the pool.

        Returns
        -------
        str:
            A string representation of the pool.
        """
        lines = [f"Pool with {self.number_of_folders} folder(s):"]
        for folder, questions in self.questions.items():
            lines.append(f"  - {folder}: {len(questions)} question(s)")
        return "\n".join(lines)

    def print_questions(self) -> None:
        """Print all questions in the pool grouped by folder."""
        first = True
        for folder, question_list in sorted(
            self.questions.items(),
            key=lambda x: x[0].name.lower(),
        ):
            if not question_list:
                continue

            if not first:
                print("\n" + "-" * 60)
            first = False

            print(f"\n\U0001f4c1 {folder}\n")
            for i, question in enumerate(question_list):
                print(f"  \U0001f4c4 Question {i + 1}")
                print(f"    Q: {question.question}")
                print("    Answers:")
                for j, ans in enumerate(question.answers):
                    mark = "✅" if j == question.right_answer else "  "
                    print(f"      {mark} {j}. {ans}")
                print("\n")


class QuestionSet(BaseModel):
    """
    A set of questions.

    The questions are grouped by a string key which usually represents a folder.

    Attributes
    ----------
    questions: dict[str, list[Question]]
        A dictionary mapping strings to lists of Question.
    """

    questions: OrderedDict[str, list[Question]]

    @model_validator(mode="before")
    @classmethod
    def fix_keys(cls, data: dict) -> dict:
        """
        Fix the keys in the questions.

        This allows to initialize the model with questions: dict[Path, list[Question]]
        instead of dict[str, list[Question]].

        Parameters
        ----------
        data : dict
            The data to fix.

        Returns
        -------
        dict:
            The fixed data.
        """
        if isinstance(data, dict) and "questions" in data:
            questions = data["questions"]
            if isinstance(questions, dict):
                data["questions"] = {str(k): v for k, v in questions.items()}
        return data

    def size(self) -> int:
        """
        Return the number of questions in the set.

        Returns
        -------
        int:
            The number of questions in the set.
        """
        return sum(len(qs) for qs in self.questions.values())

    def keys(self) -> list[str]:
        """
        Return the keys of the questions.

        Returns
        -------
        list[str]:
            The keys of the questions.
        """
        return list(self.questions.keys())

    def sample(
        self,
        n: int | list[int] | tuple[int, ...],
    ) -> list[Question]:
        """
        Sample a number of questions from the pool.

        Parameters
        ----------
        n : int | list[int] | tuple[int, ...]
            The number of questions to sample.
            If a list or tuple is provided, the number of questions to sample from
            each folder. If an integer is provided, the number of questions to sample
            from the pool.

        Returns
        -------
        list[Question]:
            A list of questions.
        """
        if isinstance(n, list | tuple):
            if len(n) != len(self.questions):
                question_keys = "\n" + "\n".join(str(k) for k in self.keys()) + "\n"
                raise ValueError(
                    f"Expected {len(self.questions)} integers "
                    "— one for each folder: "
                    f"{question_keys}but got {len(n)}.",
                )

            selected = []
            for count, folder in zip(n, self.questions, strict=False):
                items = self.questions[folder]
                if count > len(items):
                    raise ValueError(
                        f"requested {count} questions, but only {len(items)} "
                        f"are available in folder: \n{folder}",
                    )
                selected.extend(sample(items, count))

        elif isinstance(n, int):
            all_items = [q for qs in self.questions.values() for q in qs]
            if n > len(all_items):
                raise ValueError(
                    f"Requested {n} questions, but only {len(all_items)} are available"
                )
            selected = sample(all_items, n)

        else:
            raise TypeError("n must be an int, list[int], or tuple[int]")  # type: ignore[unreachable]

        return [deepcopy(d) for d in selected]


class ExamTemplate(BaseModel):
    """Pydantic-based class holding LaTeX exam configuration parts."""

    documentclass: str = "\\documentclass[11pt]{exam}\n\n"

    prebegin: str = (
        "\\usepackage{amsmath}\n"
        "\\usepackage{amssymb}\n"
        "\\usepackage{bm}\n"
        "\\usepackage{geometry}\n\n"
        "\\geometry{\n"
        "    a4paper,\n"
        "    total={160mm,250mm},\n"
        "    left=15mm,\n"
        "    right=15mm,\n"
        "    top=20mm,\n"
        "}\n\n"
        r"\linespread{1.2}"
    )

    postbegin: str = (
        "\n\\makebox[0.9\\textwidth]{Name\\enspace\\hrulefill}\n"
        "\\vspace{10mm}\n\n"
        "\\makebox[0.3\\textwidth]{Register number:\\enspace\\hrulefill}\n"
        "\\makebox[0.6\\textwidth]{School:\\enspace\\hrulefill}\n"
        "\\vspace{10mm}\n\n"
    )

    preend: str = ""
    head: str = "\n\\pagestyle{head}\n\\runningheadrule\n"
    lhead: str = ""
    chead: str = ""

    @classmethod
    def load(cls, exam_template: Path | dict | None) -> Self:
        """
        Load the exam configuration from a dict or YAML file.

        Parameters
        ----------
        exam_template : Path | dict | None
            The path to the YAML file or a dictionary.

        Returns
        -------
        ExamTemplate:
            An ExamTemplate object.
        """
        if exam_template is None:
            return cls()

        if isinstance(exam_template, Path):
            if not exam_template.is_file():
                logger.warning(
                    "The file %s does not exist. Using default configuration.",
                    exam_template,
                )
                return cls()
            with exam_template.open("r", encoding="utf-8") as f:
                exam_template = yaml.safe_load(f) or {}

        return cls(**exam_template)


class Exam(BaseModel):
    """A Pydantic model for a single exam with multiple questions."""

    exam_template: ExamTemplate
    show_answers: bool = False
    sn: str = "0"
    questions: list[Question]

    @field_validator("sn")
    @classmethod
    def validate_sn_format(cls, v: str) -> str:
        """
        Validate the format of the serial number.

        Parameters
        ----------
        v : str
            The serial number to validate.

        Returns
        -------
        str:
            The serial number.
        """
        if not v.isdigit():
            raise ValueError("Serial number (sn) must be numeric.")
        return v

    @field_validator("questions")
    @classmethod
    def validate_questions_not_empty(cls, v: list[Question]) -> list[Question]:
        """
        Validate that the exam contains at least one question.

        Parameters
        ----------
        v : list[Question]
            The questions to validate.

        Returns
        -------
        list[Question]:
            The questions.
        """
        if not v:
            raise ValueError("Exam must contain at least one question.")
        return v

    @model_validator(mode="after")
    def validate_unique_questions(self) -> Exam:
        """
        Validate that the questions are unique.

        Returns
        -------
        Exam:
            The Exam object.
        """
        seen = set()
        for q in self.questions:
            key = (q.question, tuple(q.answers))
            if key in seen:
                raise ValueError(f"Duplicate question found: '{q.question}'")
            seen.add(key)
        return self

    def apply_shuffling(
        self,
        shuffle_questions: bool = False,
        shuffle_answers: bool = False,
    ) -> None:
        """
        Apply question and/or answer shuffling in-place.

        Parameters
        ----------
        shuffle_questions : bool
            Whether to shuffle the questions.
        shuffle_answers : bool
            Whether to shuffle the answers.
        """
        if shuffle_questions:
            from random import shuffle

            shuffle(self.questions)
        if shuffle_answers:
            self.questions = [q.shuffle() for q in self.questions]

    def compile(
        self,
        path: Path | str | None,
        clean: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Compile the LaTeX exam document to PDF.

        Parameters
        ----------
        path : Path | str | None
            The path to the directory where the exams will be compiled.
        clean : bool
            Whether to clean the LaTeX auxiliary files.

        Returns
        -------
        subprocess.CompletedProcess:
            The result of the compilation.
        """
        if not path:
            path = Path(".")
        elif isinstance(path, str):
            path = Path(path)

        path.mkdir(exist_ok=True, parents=True)
        tex_file = path / "exam.tex"

        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(str(self))

        cmd = f"latexmk -pdf -cd {tex_file} -interaction=nonstopmode -f"
        logger.info("Compiling: %s", cmd)

        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                check=False,
                timeout=3600,
            )
            if result.returncode != 0:
                logger.error("LaTeX compilation failed: %s", result.stderr)
            else:
                logger.info("Compilation succeeded")

        except subprocess.TimeoutExpired as e:
            logger.exception("LaTeX compilation timed out")
            raise RuntimeError("Compilation timed out after 5 minutes") from e

        if clean:
            time.sleep(1)
            clean_cmd = f"latexmk -c -cd {tex_file}"
            try:
                subprocess.run(
                    clean_cmd.split(),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=600,
                )
            except subprocess.TimeoutExpired as e:
                logger.warning("Cleanup timed out")
                raise RuntimeError("Cleanup timed out after 10 minutes") from e

        return result

    def __str__(self) -> str:
        """
        LaTeX-ready representation of the exam.

        Returns
        -------
        str:
            A string containing the LaTeX code for the exam.
        """
        doc_parts = [
            self.exam_template.documentclass,
            self.exam_template.prebegin,
        ]

        if self.show_answers:
            doc_parts.append("\n\\printanswers\n")

        doc_parts.extend(
            [
                self.exam_template.head,
                f"\n\\rhead{{{self.sn}}}\n\n",
                self.exam_template.lhead,
                self.exam_template.chead,
                "\n\n\\begin{document}\n",
                self.exam_template.postbegin,
                "\\begin{questions}\n\n",
            ]
        )

        for q in self.questions:
            doc_parts.extend([q.to_latex()])

        doc_parts.extend(
            [
                "\n\n\\end{questions}\n\n",
                self.exam_template.preend,
                "\n\\end{document}",
            ]
        )

        return "\n".join(doc_parts)


class ExamBatch(BaseModel):
    """A batch of exams with random questions."""

    N: int
    questions_set: QuestionSet
    exam_template: ExamTemplate
    n: list[int] | tuple[int, ...] | int = field(default=1)
    exams: list[Exam] = field(default_factory=list)
    show_answers: bool = False

    @field_validator("N")
    @classmethod
    def validate_N(cls, v: int) -> int:  # noqa: N802
        """
        Validate the number of exams.

        Parameters
        ----------
        v : int
            The number of exams.

        Returns
        -------
        int:
            The number of exams.
        """
        if v <= 0:
            raise ValueError("N must be a positive integer")
        return v

    @field_validator("n", mode="before")
    @classmethod
    def validate_n_type(
        cls,
        v: int | list[int] | tuple[int, ...],
    ) -> int | list[int] | tuple[int, ...]:
        """
        Validate the type of the number of questions.

        Parameters
        ----------
        v : int | list[int] | tuple[int, ...]
            The number of questions.

        Returns
        -------
        int | list[int] | tuple[int, ...]:
            The number of questions.
        """
        if isinstance(v, int):
            if v <= 0:
                raise ValueError("Number of questions must be positive")
        elif isinstance(v, (list, tuple)):
            if not all(isinstance(x, int) and x > 0 for x in v):
                raise ValueError("All elements in 'n' must be positive integers")
        else:
            raise TypeError(
                f"'n' is {type(v)} but must be an int or list/tuple of ints"
            )
        return v

    @model_validator(mode="after")
    def validate_question_availability(self) -> ExamBatch:
        """
        Validate that the number of questions is available.

        Returns
        -------
        ExamBatch:
            The ExamBatch object.
        """
        if isinstance(self.n, int):
            if self.n > self.questions_set.size():
                raise ValueError(
                    f"Requested {self.n} questions, but only "
                    f"{self.questions_set.size()} available"
                )
        else:
            for i, (key, qlist) in enumerate(self.questions_set.questions.items()):
                if i >= len(self.n):
                    break
                if self.n[i] > len(qlist):
                    raise ValueError(
                        f"Requested {self.n[i]} questions from {key}, "
                        f"but only {len(qlist)} available"
                    )
        return self

    def make_batch(self) -> None:
        """Generate a batch of randomized exams."""
        serial_width = len(str(self.N))

        for i in range(self.N):
            try:
                questions = self.questions_set.sample(self.n)
                serial_number = str(i).zfill(serial_width)
                exam = Exam(
                    sn=serial_number,
                    exam_template=self.exam_template,
                    questions=questions,
                    show_answers=self.show_answers,
                )
                self.exams.append(exam)
                logger.debug(
                    "Created exam %s with %s questions", serial_number, len(questions)
                )
            except Exception as e:
                logger.exception("Failed to create exam %s", i)
                raise RuntimeError(f"Failed to create exam {i}") from e

        logger.info("Successfully created %s exams", len(self.exams))

    def compile(self, path: Path | str, clean: bool = False) -> None:
        """
        Compile all exams and merge into a single PDF.

        Parameters
        ----------
        path : Path | str
            The path to the directory where the exams will be compiled.
        clean : bool
            Whether to clean the LaTeX auxiliary files.
        """
        if not self.exams:
            raise RuntimeError("No exams to compile. Call make_batch() first.")

        path = Path(path).resolve()
        path.mkdir(exist_ok=True, parents=True)

        pdf_files = []
        failed = []

        for exam in self.exams:
            exam_dir = path / exam.sn
            exam_dir.mkdir(exist_ok=True, parents=True)

            try:
                logger.info("Compiling exam %s", exam.sn)
                result = exam.compile(exam_dir, clean)

                pdf_path = exam_dir / "exam.pdf"
                if result.returncode == 0 and pdf_path.exists():
                    pdf_files.append(pdf_path)
                else:
                    logger.error("PDF not created or failed for exam %s", exam.sn)
                    failed.append(exam.sn)

            except Exception:
                logger.exception("Error compiling exam %s", exam.sn)
                failed.append(exam.sn)

        if failed:
            logger.warning("Failed to compile exams: %s", ", ".join(failed))
        if not pdf_files:
            raise RuntimeError("No exams compiled successfully")

        merged_path = path / "exams.pdf"
        merger = PdfWriter()

        try:
            for pdf_path in pdf_files:
                try:
                    merger.append(pdf_path)
                except Exception:
                    logger.exception("Failed to add %s to merged PDF", pdf_path)

            with open(merged_path, "wb") as f:
                merger.write(f)

            logger.info(
                "Successfully merged %s PDFs into %s",
                len(pdf_files),
                merged_path,
            )

        except Exception as e:
            logger.exception("Failed to create merged PDF")
            raise RuntimeError("Failed to create merged PDF") from e
        finally:
            merger.close()

    def save(self, path: Path | str) -> None:
        """
        Save the batch to a YAML file.

        Parameters
        ----------
        path : Path | str
            The path to the YAML file.
        """
        path = Path(path)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(mode="json"), f, allow_unicode=True)

    @classmethod
    def load(cls, path: Path | str) -> Self:
        """
        Load a batch from a YAML file.

        Parameters
        ----------
        path : Path | str
            The path to the YAML file.

        Returns
        -------
        ExamBatch:
            An ExamBatch object.
        """
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
