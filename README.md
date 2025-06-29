# Randex: Randomized Exams

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Test](https://github.com/arampatzis/randex/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/arampatzis/randex/actions/workflows/test.yml)
[![Ruff](https://github.com/arampatzis/randex/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/arampatzis/randex/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/arampatzis/randex/branch/main/graph/badge.svg)](https://codecov.io/gh/arampatzis/randex)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![PyPI version](https://img.shields.io/pypi/v/randex.svg)](https://pypi.org/project/randex/)
[![PyPI Publish](https://img.shields.io/github/actions/workflow/status/arampatzis/randex/pypi.yml?label=Publish)](https://github.com/arampatzis/randex/actions/workflows/pypi.yml)







Randex is a library that creates exams by randomizing multiple-choice questions selected
from a user-defined pool of questions.
The final exam is generated as a LaTeX document and compiled into a PDF.
Multiple exams can be created at once.

## 🚀 Quick Start

Install `randex`:

```sh
pipx install randex
```

Download examples with questions:

```sh
randex download-examples
```

Validate the questions in the examples:

```sh
randex validate examples/en/folder_* -t examples/en/template-exam.yaml -o tmp --overwrite
```

Create a batch of exams with random questions:

```sh
randex batch "examples/en/folder_*" 5 -n 2 -t examples/en/template-exam.yaml -o tmp --overwrite --clean
```

Create a csv file with random answers to the exams in the batch:

```sh
randex random-answers -e tmp/exams.yaml
```

Grade the exams in the batch:

```sh
randex grade -e tmp/exams.yaml -g tmp/answers.csv
```



## 📦 Installation

Randex requires Python version `3.10` or higher and `latexmk`.

### Randex

To install Randex, run:

```sh
pipx install randex
```

### latexmk

In order to compile the LaTeX files, you need to install `latexmk`,

From [here](https://mg.readthedocs.io/latexmk.html):
```
Latexmk is a Perl script which you just have to run once and it does everything else for you... completely automagically.
```

and [here](https://www.cantab.net/users/johncollins/latexmk/)

```
Latexmk is also available at CTAN at https://ctan.org/pkg/latexmk/, and is/will be
in the TeXLive and MiKTeX distributions.
```

If you have already `Latex` installed in your system, you will most
probably have already `latexmk` installed as well.

## 🔧 Randex Commands

### randex download-examples

To download the latest examples from GitHub, run the following command:

```sh
randex download-examples
```

### randex validate

This command validates a single question or all questions under a folder. Execute:

```sh
randex validate "examples/en/folder_*" -t examples/en/template-exam.yaml -o tmp --overwrite
```

to validate all the questions under the folder `examples/en` that contains subfolders
with questions.
It will use the configuration from the file `examples/en/template-exam.yaml`.
The LaTeX compilation will run inside the `tmp` folder.
The `--clean` option will remove all intermediate files created by LaTeX,
and the `-a` flag will show the correct answers in the produced PDF.
Open the PDF file inside `tmp` to validate that all questions appear correctly.

Run:

```sh
randex validate --help
```

to see the help message for the command.

### randex batch

To create a batch of exams with random questions, execute:

```sh
randex batch "examples/en/folder_*" 5 -n 2 -t examples/en/template-exam.yaml -o tmp --overwrite --clean
```

This command will create 5 exams using the questions inside the 3 folders with
names `folder_0`, `folder_1`, and `folder_2` using the configuration from the file
`examples/en/template-exam.yaml`.
The `--clean` option will remove all intermediate files created by LaTeX.
The `-n` option specifies the number of questions randomly chosen from each folder.
It can appear once, meaning all folders will contribute the same number of questions,
or multiple times, e.g., `-n 2 -n 1 -n 3`, indicating the first folder will contribute
2 questions, the second folder will contribute 1 question, and the third folder will
contribute 3 questions.
The batch size (5 in this example) specifies the number of exams to create.

### Grade

First create a batch of exams in a `tmp` folder.
Then create a csv file with random answers to the exams,

```sh
randex random-answers -e tmp/exams.yaml
```

Then grade the exams,

```sh
randex grade -e tmp/exams.yaml -g tmp/answers.csv
```

The `-n` option can be used to specify the negative score for each wrong answer.
If not provided, the negative score is computed as `1 / (number of answers - 1)`
for each question.
Set it to `0` to disable the negative scoring.


## 📁 Randex Data Scheme

Randex requires two types of data files to create the exams.

### template-exam.yaml File

The `template-exam.yaml` file is a `YAML` file that describes the LaTeX file that will
produce the exam. It contains the following keys:

- `documentclass` (optional): String with the documentclass command of the file.
Only the `exam` class is supported. Default:
    ```latex
    \documentclass[11pt]{exam}
    ```
- `prebegin` (optional): String containing everything that goes before the
`\begin{document}` command. Default:
    ```latex
    \usepackage{amsmath}
    \usepackage{amssymb}
    \usepackage{bm}
    \usepackage{geometry}

    \geometry{
        a4paper,
        total={160mm,250mm},
        left=15mm,
        right=15mm,
        top=20mm,
    }

    \linespread{1.2}
    \pagestyle{head}
    \runningheadrule
    ```
- `postbegin` (optional): String with all the commands right after the "\begin{document}" command. Default: empty string.
- `preend` (optional): String with all the commands right before the "\end{document}" command. Default: empty string.
- `lhead` (optional): String that is displayed on the left part of the head. Default: empty string
- `chead` (optional): String that is displayed on the center part of the head. Default: empty string

The right part of the head is reserved for the serial number of the exam.

### questions.yaml File

Each question is written in a `YAML` file with the following keys:

- `question` (required): String with the question. Do not use double quotes around the string.
- `answers` (required): List of strings with the answers. Do not use double quotes around the strings.
- `right_answer` (required): Integer indicating the correct answer.
The answer is non-negative and less than the length of the `answers` list.

The questions `YAML` files should be organized inside folders.

The `randex` commands take the `template-exam.yaml` file and the folders containing the questions as inputs.



## 📄 License

Licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
Commercial use is prohibited without prior permission.
