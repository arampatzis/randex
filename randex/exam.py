"""
Implementation of the Question and the Exam classes.
These classes are the building block of the library.
"""
import subprocess
import sys
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from random import sample, shuffle
from typing import TypeVar

from typing_extensions import Self
from cerberus import TypeDefinition
from pypdf import PdfWriter

from randex.schema import validate, RandexValidator
from randex.load_dump import yaml_dump

T = TypeVar("T")
LT = list[T] | tuple[T, ...]


@dataclass(kw_only=True)
class Pool:
    folders: LT[Path]
    # List or tuple of folders containing questions in YAML files

    files: list[list[Path]] = field(default_factory=lambda: [])
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
        if not num_items:
            num_items = [1 for _ in self.folders]

        fs = []
        for k, files in enumerate(self.files):

            if num_items[k] > len(files):
                raise ValueError("The")

            fs += sample(files, num_items[k])

        index = list(range(len(fs)))
        shuffle(index)

        return [fs[i] for i in index]

    @classmethod
    def get_schema(cls) -> str:
        """Return the data schema of the dataclass."""
        return {
            'folders': {
                'type': 'list',
                'schema': {
                    'type': 'path',
                    'coerce': Path,
                },
            },
            'N':{
                'type': 'integer',
                'coerce': int,
                'required': False,
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
            'files': {
                'type': 'list',
                'required': False,
                'schema': {
                    'type': 'list',
                    'schema': {
                        'type': 'path',
                        'coerce': Path
                    },
                },
            },
        }
        

@dataclass(kw_only=True)
class Question:
    """A dataclass for the exam questions."""

    question: str
    answers: list[str]
    right_answers: list[str]

    def randomize(self):
        """Randomize the order of the questions."""
        index = list(range(len(self.answers)))
        shuffle(index)

        self.answers = [self.answers[i] for i in index]
        self.right_answers = [index[i] for i in self.right_answers]

    def __str__(self):
        """Return a latex-ready string of the question."""
        qdoc = []
        qdoc += [r"\item " + self.question]
        qdoc += ["\\begin{tasks}[label-format={\\bfseries}](3)"]
        qdoc += ["    \\task " + k for k in self.answers]
        qdoc += ["\\end{tasks}"]

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
        }


RandexValidator.types_mapping['Question'] = TypeDefinition('Question', (Question,), ())


@dataclass(kw_only=True)
class Header:
    """Dataclass that holds the basic elements of a latex exam document."""

    documentclass: str
    usepackage: str
    prebegin: str
    postbegin: str

    @classmethod
    def load(self, header: Path | dict | None) -> Self:
        """Load the header parts of the exam."""
        if not header:
            header = {}

        elif isinstance(header, Path) and not header.is_file():
            print(f"The file {header} does not exist. Using the default header.")
            header = {}

        cfg = validate(Header.get_schema(), header)
        return Header(**cfg)

    @classmethod
    def get_schema(cls) -> str:
        """Return the data schema of the dataclass."""
        return {
            "documentclass": {
                "type": "string",
                "required": False,
                "default": "\\documentclass[11pt]{article}\n\n",
            },
            "usepackage": {
                "type": "string",
                "required": False,
                "default": (
                    "\\usepackage{amsmath}\n"
                    "\\usepackage{amssymb}\n"
                    "\\usepackage{bm}\n"
                    "\\usepackage{geometry}\n\n"
                ),
            },
            "prebegin": {
                "type": "string",
                "required": False,
                "default": (
                    "\n\\geometry{\n"
                    "    a4paper,\n"
                    "    total={160mm,250mm},\n"
                    "    left=15mm,\n"
                    "    right=15mm,\n"
                    "    top=20mm,\n"
                    "}\n\n"
                ),
            },
            "postbegin": {
                "type": "string",
                "required": False,
                "default": "",
            },
        }


RandexValidator.types_mapping['Header'] = TypeDefinition('Header', (Header,), ())


@dataclass(kw_only=True)
class Exam:
    """A dataclass for a single exam with multiple questions."""

    header: Header

    sn: int = 0
    
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
                except RuntimeError as e:
                    print(f"Error while loading {q}.")
                    print(e)
                    sys.exit()

                self.questions += [Question(**cfg)]
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

        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=False,
        )

        if clean:
            import time

            time.sleep(0.5)
            cmd = f"latexmk -c -cd {path}/question.tex"
            print(cmd)
            subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                check=False,
            )

        return result

    def __str__(self):
        """Latex-ready representation of the exam."""
        doc = self.header.documentclass
        doc += self.header.usepackage

        doc += "\\usepackage{tasks}\n"

        doc += self.header.prebegin

        doc += "\n\\begin{document}\n"
        doc += self.header.postbegin

        doc += "\n\\begin{enumerate}\n"

        for q in self.questions:
            q.randomize()
            doc += "\n" + str(q) + "\n"

        doc += "\n\\end{enumerate}\n"

        doc += "\n\\end{document}"

        return doc

    @classmethod
    def get_schema(cls) -> dict:
        """Schema of the configuration."""
        return {
            'header': {
                'type': 'Header',
                'required': True,
            },
            'sn': {
                'type': 'integer',
                'required': False,
                'default': 1,
                'coerce': int,
            },
            'questions': {
                'type': 'list',
                'schema': {
                    'type': 'Question',
                },
                'required': False,
                'nullable': True,
            },
        }


@dataclass(kw_only=True)
class ExamBatch:
    N: int
    # Number of exams in the batch

    pool: Pool
    # Pool object with the availabe questions

    header: Header
    # Latex header class

    n: list[int] | int = field(default=1)
    # Number of questions per folder in pool

    exams: list[Exam] = field(default_factory=list)
    # List with all exams

    def __post_init__(self):
        
        if isinstance(self.n, int | float):
            self.n = [self.n for i in self.pool.n]

        else:
            if len(self.n) != self.pool.N:
                print("Error: len(self.n) != self.pool.N")
                sys.exit()

            for i in range(self.pool.N):
                if self.n[i] > self.pool.n[i]:
                    print(f"n1 > n2... {self.pool.folders[i]}")
                    self.n[i] = self.pool.n[i]

    def make_batch(self):
        """Make a batch of exams"""
        for i in range(self.N):
            qs = self.pool.get_questions(self.n)

            e = Exam(sn=i, header=self.header)
            for q in qs:
                e.add_question(q)

            self.exams.append(e)
    
    def dump(self, path: Path):
        """Save the exams in YAML"""
        path = path.resolve()
        if path.suffix not in ('.yaml', '.yml'):
            print('The extension of {path} is not yaml or yml.')
            exit()
        path.parent.mkdir(exist_ok=True, parents=True)
        yaml_dump(asdict(self), path)

    @staticmethod
    def load( path: Path) -> Self:
        """Load a batch exam YAML file"""
        with open('data.yml', 'r') as f:
            d = yaml.safe_load(f)
        
        cfg = validate(Pool.get_schema(), d['pool'])
        pool = Pool(**cfg)

        exams = []
        for e in d['exams']:
            cfg = validate(Header.get_schema(), e['header'])
            header = Header(**cfg)
            
            questions = []
            for q in e['questions']:
                cfg = validate(Question.get_schema(), q)
                questions.append(Question(**cfg))
            
            cfg = {
                'header': header,
                'sn': e['sn'],
                'questions': questions,
            }
            cfg = validate(Exam.get_schema(), cfg)
            exams.append(Exam(**cfg))

        cfg = validate(Header.get_schema(), d['header'])
        header = Header(**cfg)    
        
        cfg = {
            'pool': pool,
            'header': header,
            'exams': exams,
            'n': [int(i) for i in d['n']],
            'N': int(d['N']),
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
            pdfs.append(p / 'exam.pdf')
            
        merger = PdfWriter()
        for pdf in pdfs:
            merger.append(pdf)

        merger.write(path / 'exams.pdf')
        merger.close()