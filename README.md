# Randex: Randomized Exams

This library creates exams by
randomizing multiple choice questions chosen from a user-defined
pool of questions. 
The final exam is a latex document that is compiled into a pdf.
Multiple exams can be created at once.

# Installation

The minimum Python version needed for this project is `3.10`.

## Poetry

[Poetry](https://python-poetry.org)
is the packaging and dependecy manager used in this project.
To install Poetry see the instructions [here](https://python-poetry.org/docs/#installing-with-pipx).

## Randex

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

# Randex commands

Inside an acticated environemnt you can run on of the next commands.

## Validate

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
