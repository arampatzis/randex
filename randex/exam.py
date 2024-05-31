"""
Implementation of the Question and the Exam classes.
These classes are the building block of the library.
"""
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from random import sample, shuffle
from typing import TypeVar

import yaml
from cerberus import TypeDefinition
from pypdf import PdfWriter
from typing_extensions import Self

from randex.load_dump import yaml_dump
from randex.schema import RandexValidator, validate

T = TypeVar("T")
LT = list[T] | tuple[T, ...]


@dataclass(kw_only=True)
class Pool:
    """A collection of folders containg questions in YAML format"""

    folders: LT[Path]
    # List or tuple of folders containing questions in YAML files

    files: list[list[Path]] = field(default_factory=list)
    # A list with the YAML files per folder

    N: int = 0
    # Number of folders in the pool

    n: list[int] = field(default_factory=list)
    # Number of files in every folder

    def __post_init__(self):
        for f in self.folders:
            if not f.is_dir():
                raise RuntimeError(f"{f} is not a valid folder.")

        self.n = []
        for f in self.folders:
            g = list(f.resolve().glob("**/*.yaml"))
            n = len(g)

            if n < 1:
                raise RuntimeError(f"{f} does not contain any YAML files.")

            self.n.append(n)
            self.files.append(g)

        self.N = len(self.folders)

    def get_questions(self, num_items: list[int] | None = None):
        """
        Get num_items questions from the pool. num_items is a list, and each
        items corresponds to the number of questions chosen from one folder.
        """
        if not num_items:
            num_items = [1 for _ in self.folders]

        fs = []
        for k, files in enumerate(self.files):
            if num_items[k] > len(files):
                raise ValueError("TODO...")

            fs += sample(files, num_items[k])

        index = list(range(len(fs)))
        shuffle(index)

        return [fs[i] for i in index]

    @classmethod
    def get_schema(cls) -> str:
        """Return the data schema of the dataclass."""
        return {
            "folders": {
                "type": "list",
                "schema": {
                    "type": "path",
                    "coerce": Path,
                },
            },
            "N": {
                "type": "integer",
                "coerce": int,
                "required": False,
            },
            "n": {
                "type": "list",
                "required": False,
                "nullable": True,
                "coerce": lambda v: [int(i) for i in v],
                "schema": {
                    "type": "integer",
                },
            },
            "files": {
                "type": "list",
                "required": False,
                "schema": {
                    "type": "list",
                    "schema": {
                        "type": "path",
                        "coerce": Path,
                    },
                },
            },
        }


@dataclass(kw_only=True)
class Question:
    """A dataclass for the exam questions."""

    question: str
    answers: list[str]
    right_answers: list[int]
    points: int = 1
    n: int = field(init=False)

    def __post_init__(self):
        self.n = len(self.answers)

    def randomize(self):
        """Randomize the order of the questions."""
        index = list(range(len(self.answers)))
        shuffle(index)

        self.answers = [self.answers[i] for i in index]
        self.right_answers = [index.index(i) for i in self.right_answers]

    def __str__(self):
        """Return a latex-ready string of the question."""
        qdoc = []
        qdoc += [f"\\question[{self.points}]" + self.question]
        qdoc += ["\n\\begin{oneparchoices}"]

        for i in range(len(self.answers)):
            s = "\\correctchoice " if i in self.right_answers else "\\choice "

            qdoc += ["    " + s + self.answers[i]]

        qdoc += ["\\end{oneparchoices}"]

        return "\n".join(qdoc)

    @classmethod
    def get_schema(cls) -> str:
        """Return the data schema of the dataclass."""
        return {
            "question": {
                "type": "string",
                "required": True,
            },
            "answers": {
                "type": "list",
                "required": True,
                "coerce": lambda v: [str(i) for i in v],
                "schema": {
                    "type": "string",
                },
            },
            "right_answers": {
                "type": "list",
                "leq_length": "answers",
                "elements_leq_length": "answers",
                "check_with": "nonnegative_elements",
                "required": True,
                "coerce": lambda v: [int(i) for i in v],
                "schema": {
                    "type": "integer",
                },
            },
            "points": {
                "type": "integer",
                "check_with": "positive",
                "required": True,
            },
        }


RandexValidator.types_mapping["Question"] = TypeDefinition("Question", (Question,), ())


@dataclass(kw_only=True)
class Tex:
    """Dataclass that holds the basic elements of a latex exam document."""

    documentclass: str
    prebegin: str
    postbegin: str
    preend: str
    lhead: str = ""
    chead: str = ""
    _head: str = field(init=False)

    def __post_init__(self):
        self._head = "\n\\pagestyle{head}\n" "\\runningheadrule\n"

    @property
    def head(self):
        """Return the protected variable _head"""
        return self._head

    @staticmethod
    def load(tex: Path | dict | None) -> Self:
        """Load the tex parts of the exam."""
        if not tex:
            tex = {}

        elif isinstance(tex, Path) and not tex.is_file():
            print(
                f"The file {tex} does not exist. Using the default exam configuration.",
            )
            tex = {}

        cfg = validate(Tex.get_schema(), tex)
        return Tex(**cfg)

    @classmethod
    def get_schema(cls) -> str:
        """Return the data schema of the dataclass."""
        return {
            "documentclass": {
                "type": "string",
                "required": False,
                "default": "\\documentclass[11pt]{exam}\n\n",
            },
            "prebegin": {
                "type": "string",
                "required": False,
                "default": (
                    "\\usepackage{amsmath}\n"
                    "\\usepackage{amssymb}\n"
                    "\\usepackage{bm}\n"
                    "\\usepackage{geometry}\n\n"
                    "\n\\geometry{\n"
                    "    a4paper,\n"
                    "    total={160mm,250mm},\n"
                    "    left=15mm,\n"
                    "    right=15mm,\n"
                    "    top=20mm,\n"
                    "}\n\n"
                    r"\linespread{1.2}"
                ),
            },
            "postbegin": {
                "type": "string",
                "required": False,
                "default": (
                    "\n\\makebox[0.9\\textwidth]{Name\\enspace\\hrulefill}\n"
                    "\\vspace{10mm}\n\n"
                    "\\makebox[0.3\\textwidth]{Register number:\\enspace\\hrulefill}\n"
                    "\\makebox[0.6\\textwidth]{School:\\enspace\\hrulefill}\n"
                    "\\vspace{10mm}\n\n"
                ),
            },
            "preend": {
                "type": "string",
                "required": False,
                "default": "",
            },
            "lhead": {
                "type": "string",
                "required": False,
                "default": "",
            },
            "chead": {
                "type": "string",
                "required": False,
                "default": "",
            },
        }


RandexValidator.types_mapping["Tex"] = TypeDefinition("Tex", (Tex,), ())


@dataclass(kw_only=True)
class Exam:
    """A dataclass for a single exam with multiple questions."""

    tex: Tex

    show_answers: bool = False

    sn: str = "0"

    questions: list[Question] = field(default_factory=list)

    def add_question(self, qpath: Path):
        """Add a question to the exam."""
        q_schema = Question.get_schema()

        if qpath.is_file():
            try:
                cfg = validate(q_schema, qpath)
            except RuntimeError as e:
                raise RuntimeError(f"Error in while loading {qpath}") from e

            self.questions += [Question(**cfg)]
            return

        if qpath.is_dir():
            for q in qpath.glob("**/*.yaml"):
                try:
                    cfg = validate(q_schema, q)
                    self.questions += [Question(**cfg)]
                except RuntimeError as e:
                    print("No question added.")
                    print(f"Skip {q} because of error:")
                    print("\t".join(("\n" + str(e).lstrip()).splitlines(True)))

            return

    def compile(
        self,
        path: Path | str | None,
        clean: bool = False,
    ):
        """Compile the latex exam document to pdf"""
        if not path:
            path = Path(".")

        if isinstance(path, str):
            path = Path(path)

        path.mkdir(exist_ok=True, parents=True)

        with open(path / "exam.tex", "w") as f:
            f.write(str(self))

        cmd = f"latexmk -pdf -cd {path}/exam.tex -interaction=nonstopmode -f"
        print(cmd)
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=False,
        )

        if clean:
            import time

            time.sleep(1)
            cmd = f"latexmk -c -cd {path}/exam.tex"
            subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                check=False,
            )

        return result

    def __str__(self):
        """Latex-ready representation of the exam."""
        doc = self.tex.documentclass
        doc += self.tex.prebegin

        if self.show_answers:
            doc += "\n\n\\printanswers\n\n"

        doc += self.tex.head
        doc += f"\n\\rhead{{{self.sn}}}\n\n"
        doc += self.tex.lhead
        doc += self.tex.chead

        doc += "\n\n\\begin{document}\n"
        doc += self.tex.postbegin

        doc += "\\begin{questions}\n\n"
        for q in self.questions:
            q.randomize()
            doc += "\n" + str(q) + "\n"
        doc += "\n\n\\end{questions}\n\n"

        doc += self.tex.preend

        doc += "\n\\end{document}"

        return doc

    @classmethod
    def get_schema(cls) -> dict:
        """Return the schema of the configuration."""
        return {
            "tex": {
                "type": "Tex",
                "required": True,
            },
            "sn": {
                "type": "string",
                "required": False,
                "default": "0",
                "coerce": str,
            },
            "questions": {
                "type": "list",
                "schema": {
                    "type": "Question",
                },
                "required": False,
                "nullable": True,
            },
            "show_answers": {
                "type": "boolean",
                "required": False,
                "default": False,
            },
        }


@dataclass(kw_only=True)
class ExamBatch:
    """A batch of exams with random questions."""

    N: int
    # Number of exams in the batch

    pool: Pool
    # Pool object with the availabe questions

    tex: Tex
    # Tex class with all the exam components except the questions

    n: list[int] | int = field(default=1)
    # Number of questions per folder in pool

    exams: list[Exam] = field(default_factory=list)
    # List with all exams

    def __post_init__(self):
        if not self.n:
            print(f"Invalid value for number of question per folder: {self.n}")

        if isinstance(self.n, int | float):
            self.n = [self.n for _ in self.pool.n]

        else:
            self.n = list(self.n)
            if len(self.n) < self.pool.N:
                k = self.pool.N - len(self.n)
                self.n.extend(k * [self.n[-1]])

            for i in range(self.pool.N):
                if self.n[i] > self.pool.n[i]:
                    print(f"n1 > n2... {self.pool.folders[i]}")
                    self.n[i] = self.pool.n[i]

    def make_batch(self):
        """Make a batch of exams"""
        N = len(str(self.N))

        for i in range(self.N):
            qs = self.pool.get_questions(self.n)
            sn = str(i).zfill(N)
            e = Exam(sn=sn, tex=self.tex)
            for q in qs:
                e.add_question(q)

            self.exams.append(e)

    def dump(self, path: Path):
        """Save the exams in YAML"""
        path = path.resolve()
        if path.suffix not in (".yaml", ".yml"):
            print("The extension of {path} is not yaml or yml.")
            sys.exit()
        path.parent.mkdir(exist_ok=True, parents=True)
        yaml_dump(asdict(self), path)

    @staticmethod
    def load(path: Path) -> Self:
        """Load a batch exam YAML file"""
        with open(path) as f:
            d = yaml.safe_load(f)

        cfg = validate(Pool.get_schema(), d["pool"])
        pool = Pool(**cfg)

        exams = []
        for e in d["exams"]:
            cfg = validate(Tex.get_schema(), e["tex"])
            tex = Tex(**cfg)

            questions = []
            for q in e["questions"]:
                cfg = validate(Question.get_schema(), q)
                questions.append(Question(**cfg))

            cfg = {
                "tex": tex,
                "sn": e["sn"],
                "questions": questions,
            }
            cfg = validate(Exam.get_schema(), cfg)
            exams.append(Exam(**cfg))

        cfg = validate(Tex.get_schema(), d["tex"])
        tex = Tex(**cfg)

        cfg = {
            "pool": pool,
            "tex": tex,
            "exams": exams,
            "n": [int(i) for i in d["n"]],
            "N": int(d["N"]),
        }
        return ExamBatch(**cfg)

    def compile(self, clean: bool, path: Path):
        """Compile all exams"""
        pdfs = []

        for e in self.exams:
            print(e.sn)
            p = path / str(e.sn)
            p.mkdir(exist_ok=True, parents=True)
            e.compile(p, clean)
            pdfs.append(p / "exam.pdf")

        merger = PdfWriter()
        for pdf in pdfs:
            merger.append(pdf)

        merger.write(path / "exams.pdf")
        merger.close()
