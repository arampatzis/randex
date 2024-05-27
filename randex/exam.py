from pathlib import Path
from dataclasses import dataclass
import yaml
import subprocess

from randex.schema import validate
from random import shuffle

@dataclass(kw_only=True)
class Question:
    
    question: str
    answers: list[str]
    right_answers: list[str]

    def randomize(self):
        index = list(range(len(self.answers)))
        shuffle(index)
        
        self.answers = [self.answers[i] for i in index]
        self.right_answers = [index[i] for i in self.right_answers]

    def __str__(self):
        
        qdoc = []
        qdoc += ["\item " + self.question]
        qdoc += ["\\begin{tasks}[label-format={\\bfseries}](3)"]
        qdoc += ["    \\task " + k for k in self.answers]
        qdoc += ["\\end{tasks}"]
        
        return "\n".join(qdoc)
    
    @classmethod
    def get_schema(cls, ) -> str:
        
         schema = {
            'question': {
                'type': 'string',
                'required': True,
            },
            'answers': {
                'type': 'list',
                'required': True,
                'coerce': lambda v: [str(i) for i in v],
                'schema':{
                    'type': 'string',
                }
            },
            'right_answers': {
                'type': 'list',
                'leq_length': 'answers',
                'elements_leq_length': 'answers',
                'check_with': 'nonnegative_elements',
                'required': True,
                'coerce': lambda v: [int(i) for i in v],
                'schema':{
                    'type': 'integer',
                }
            },
         }
         return schema
    
    
@dataclass(kw_only=True)
class Header:
    
    documentclass: str
    usepackage: str
    prebegin: str
    postbegin: str
    
    @classmethod
    def get_schema(cls, ) -> str:
        
        schema = {
            'documentclass': {
                'type': 'string',
                'required': False,
                'default': '\documentclass[11pt]{article}\n\n'
            },
            'usepackage': {
                'type': 'string',
                'required': False,
                'default': (
                    "\\usepackage{amsmath}\n"
                    "\\usepackage{amssymb}\n"
                    "\\usepackage{bm}\n"
                    "\\usepackage{geometry}\n\n"
                ),
            },
            'prebegin': {
                'type': 'string',
                'required': False,
                'default': (
                    "\n\geometry{\n"
                    "    a4paper,\n"
                    "    total={160mm,250mm},\n"
                    "    left=15mm,\n"
                    "    right=15mm,\n"
                    "    top=20mm,\n"
                    "}\n\n"
                ),
            },
            'postbegin': {
                'type': 'string',
                'required': False,
                'default': "",
            },
        }
        return schema
 
 
class Exam:
    
    def __init__(self):
        
        self._questions: list[Question] = []
        
        self._header: Header | None = None
    
    def load_header(self, hpath: Path | dict | None):    
        
        if not hpath:
            hpath = {}
        
        elif not hpath.is_file():
            print(f"The file {hpath} does not exist. Using the default header.")
            hpath = {}

        cfg = validate(Header.get_schema(), hpath)
        self._header = Header(**cfg)
     
    def add_question(self, qpath: Path):
        """Add a question to the exam."""
        
        q_schema = Question.get_schema()
        
        if qpath.is_file():
            try:
                cfg = validate(q_schema, qpath)
            except RuntimeError as e:
                raise Exception(f"Error in while loading {qpath}") from e
                
            self._questions += [Question(**cfg)]
            return
        
        if qpath.is_dir():
            for q in qpath.glob('**/*.yaml'):
                try:
                    cfg = validate(q_schema, q)
                except RuntimeError as e:
                    print(f"Error while loading {q}.")
                    print(e)
                    exit()
                    
                self._questions += [Question(**cfg)]
            return

        
    def compile(self, path: Path | str | None):
        """Compile the exam document"""
        
        if not path:
            path = Path('.')
        
        if isinstance(path, str):
            path = Path(path)
        
        path.mkdir(exist_ok=True, parents=True)
        
        with open(path / "question.tex", "w") as f:
            f.write(str(self))
        
        cmd = f"latexmk -pdf -cd {path}/question.tex -interaction=nonstopmode -f" 
        
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            check=False
        )
        
        return result
        
    def __str__(self):
                
        doc = self._header.documentclass
        doc += self._header.usepackage
        
        doc += "\\usepackage{tasks}\n"
        
        doc += self._header.prebegin
        
        doc += "\n\\begin{document}\n"
        doc += self._header.postbegin
        
        doc += "\n\\begin{enumerate}\n"
        
        for q in self._questions:
            q.randomize()
            doc += "\n" + str(q) + "\n"
        
        doc += "\n\\end{enumerate}\n"
        
        doc += "\n\\end{document}"
        
        return doc
    