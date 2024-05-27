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

### Header

The header file is a `YAML` file that describes the latex file that will prodice the exam.
It contains the following keys:
* `documentclass` (optional): String with the documentclass command of the file. Default:
```latex
\documentclass[11pt]{article}
```
* `usepackage` (optional): String with all the needed usepackage commands. Default:
```latex
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{bm}
\usepackage{geometry}
```
* `prebegin` (optional): String with all the commands right before the `\begin{document}` command. Default:
```latex
\geometry{
    a4paper,
    total={160mm,250mm},
    left=15mm,
    right=15mm,
    top=20mm,
}
```
* `postbegin` (optional): String with all the commands right after the `\begin{document}` command. Default: empty string.

### Questions

Each question is written in a `YAML` file with the following keys:
* `question` (required): String with the question. Do not use double quotes around the string.
* `answers` (required): A list of strings with the answers. Do not use double quotes around the string.
* `right_answers` (required): A list of integers with the correct answers.
The questions are numbered from zero.
The elements of the list are non-negative and less than the length of the list `answers`.

The questions `YAML` files should be organized inside folders.

The exam creations command gets as an input the header file and the folders containing the exams.


# Randex commands

Inside an acticated environemnt you can run on of the next commands.

### Validate

This command validates a single question or all questions inside a folder.
Execute
```bash
validate example/folder_1/ -a temp -h example/header.yaml
```
in order to validate all the questions inside the folder `example/folder_1/`
using the header file in `example/header.yaml`.
The latex compilation will run inside the `temp` folder.
Open the pdf file inside `temp` to validate that all the questions appear
correcly.

Run
```bash
validate --help
```
to see the help message of the command.

### Exams

### Grade
