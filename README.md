# Randex: Randomized Exams

This library creates exams by
randomizing multiple choice questions chosen from a user-defined
pool of questions.
The final exam is a latex document that is compiled into a pdf.
Multiple exams can be created at once.

# Installation

The minimum Python version needed for this project is `3.10`.

### Poetry

[Poetry](https://python-poetry.org)
is the packaging and dependecy manager used in this project.
To install Poetry see the instructions [here](https://python-poetry.org/docs/#installing-with-pipx).

### Randex

To install the library run the following command from the root folder
of the project
```sh
poetry install
```
and then execute
```bash
poetry shell
```
to spawn a shell with the Python environment activated.

# Randex data scheme

The library requires two types of data files in order to create the exams.

### Tex

The `Tex` file is a `YAML` file that describes the latex file that will produce the exam.
It contains the following keys:
* `documentclass` (optional): String with the documentclass command of the file. Only the `exam`
class is supported. Default:
```latex
\documentclass[11pt]{exam}
```
* `prebegin` (optional): String that contains everything that goes before the the `\begin{document}` command.. Default:
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
* `postbegin` (optional): String with all the commands right after the `\begin{document}` command. Default: empty string.

* `preend` (optional): String with all the commands right before the `\end{document}` command. Default: empty string.


### Questions

Each question is written in a `YAML` file with the following keys:
* `question` (required): String with the question. Do not use double quotes around the string.
* `answers` (required): A list of strings with the answers. Do not use double quotes around the string.
* `right_answers` (required): A list of integers with the correct answers.
The questions are numbered from zero.
The elements of the list are non-negative and less than the length of the list `answers`.
* `points` (optional): The points given to the question. Default: `1`

The questions `YAML` files should be organized inside folders.

The `randex` commands gets as an input the `Tex` file and the folders containing the exams.


# Randex commands

Inside an acticated environemnt you can run on of the next commands.

### Validate

This command validates a single question or all questions inside a folder.
Execute
```bash
validate example/en -t example/en/tex.yaml -o temp --clean -a
```
in order to validate all the questions inside the folder `example/en`
that contains subfolders with questions.
It will use the configuration from the file `example/en/tex.yaml`.
The latex compilation will run inside the `temp` folder.
The `--clean` will remove all intermediate created files from Latex and the
`-a` flag will show the correct answers in the produced pdf.
Open the pdf file inside `temp` to validate that all the questions appear
correcly.

Run
```bash
validate --help
```
to see the help message of the command.

### Exams

In order to create a batch of exams with random questions, execute
```bash
exams example/en/folder_0/ example/en/folder_1/ example/en/folder_2/ -b 10 -t example/en/tex.yaml --clean -n 2
```
This command will create 10 exams from 3 folders using the configuration from the file `example/en/tex.yaml`.
The `--clean` will remove all intermediate created files from Latex.
The `-n` option is the number of questions randomly chose from every folder.
It can appear only once and all the folders will be represented by the same number of questions.
Or it can appear more that once, e.g., `-n 2 -n 1`, indicating that the first folder as appeared in the
command line will be represented by two questions, and the rest folders by 1 question.
One more example, the case `-n 2 -n 1 -n 3` indicates that the first, second, and third folder will
be represented by 2, 1, and 3 questions, respectively.

### Grade

Not implemented yet.
