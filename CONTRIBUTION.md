# Contributing to Randex

Welcome to Randex! This document provides instructions for developers working on the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Poetry](#poetry)
- [Testing](#testing)
- [Documentation](#documentation)
- [Code Quality](#code-quality)
- [Versioning](#versioning)
- [Publishing to PyPI](#publishing-to-pypi)
- [Project Structure](#project-structure)
- [Git Workflow](#git-workflow)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- latexmk (for LaTeX compilation)

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/arampatzis/randex.git
   cd randex
   ```

2. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Activate the virtual environment:
   ```bash
   poetry shell
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Poetry

This project uses Poetry for dependency management and packaging.

### Key Commands

- **Install dependencies**: `poetry install`
- **Add a new dependency**: `poetry add <package-name>`
- **Add a development dependency**: `poetry add --group dev <package-name>`
- **Update dependencies**: `poetry update`
- **Show dependencies**: `poetry show`
- **Remove a dependency**: `poetry remove <package-name>`
- **Build the package**: `poetry build`
- **Publish to PyPI**: `poetry publish`

### Working with Dependencies

- **Production dependencies** go in `[tool.poetry.dependencies]`
- **Development dependencies** go in `[tool.poetry.group.dev.dependencies]`

Example adding a new dependency:
```bash
# Production dependency
poetry add pydantic

# Development dependency
poetry add --group dev pytest
```

### Scripts

The project defines several CLI scripts in `pyproject.toml`:
- `exams`: Main command for creating exam batches
- `validate`: Command for validating questions
- `randex-download-examples`: Download example files

## Testing

We use pytest for testing with comprehensive test coverage.

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=randex

# Run specific test types using markers
poetry run pytest -m unit        # Unit tests
poetry run pytest -m integration # Integration tests
poetry run pytest -m slow        # Slow tests

# Run tests in verbose mode
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_exam.py

# Run specific test function
poetry run pytest tests/test_exam.py::test_create_valid_exam
```

### Test Organization

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test complete workflows and component interactions
- **Slow tests**: Long-running tests that might be skipped in development

### Test Structure

Tests are organized in the `tests/` directory:
- `conftest.py`: Shared fixtures and configuration
- `test_*.py`: Individual test modules
- Test fixtures provide sample data and temporary directories

### Writing Tests

1. Use descriptive test names starting with `test_`
2. Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
3. Use fixtures from `conftest.py` for sample data
4. Test both success and failure cases
5. Include docstrings for complex tests

Example test:
```python
@pytest.mark.unit
def test_question_validation(self, sample_question_data):
    """Test that Question validates input data correctly."""
    question = Question(**sample_question_data)
    assert question.question == sample_question_data["question"]
    assert len(question.answers) == len(sample_question_data["answers"])
```

## Documentation

### Docstring Style

We use **NumPy-style docstrings** throughout the codebase.
All public functions, classes, and methods must have docstrings.

#### Function Docstring Template:
```python
def example_function(param1: str, param2: int = 5) -> bool:
    """
    Brief description of the function.

    Longer description if needed. Explain the purpose,
    behavior, and any important details.

    Parameters
    ----------
    param1 : str
        Description of param1.
    param2 : int, optional
        Description of param2, by default 5.

    Returns
    -------
    bool
        Description of return value.

    Raises
    ------
    ValueError
        Description of when this exception is raised.

    Examples
    --------
    >>> example_function("hello", 10)
    True
    """
```

#### Class Docstring Template:
```python
class ExampleClass:
    """
    Brief description of the class.

    Longer description explaining the purpose and usage
    of the class.

    Attributes
    ----------
    attribute1 : str
        Description of attribute1.
    attribute2 : int
        Description of attribute2.
    """
```


### Type Hints

- All functions must include type hints
- Use `from __future__ import annotations` for forward references
- Import types from `typing` or `typing_extensions` as needed
- Complex types should be clearly documented

## Code Quality

### Pre-commit Hooks

Install pre-commit hooks in the root folder of the project:
```bash
pre-commit install
```

Pre-commit hooks run **automatically** on every `git commit`
and will prevent the commit if any checks fail. The hooks include:
- ruff linting and formatting
- mypy type checking
- Various file and syntax checks

If a hook fails, fix the issues and commit again.
    Most formatting issues are automatically fixed by the hooks.

If you want to run the pre-commit hooks manually, run:
```bash
pre-commit run --all-files
```
If you want to run the pre-commit for a specific hook id, run:
```bash
pre-commit run <hook-id> --all-files
```

### Code Style Guidelines

1. Follow PEP 8 style guidelines
2. Use double quotes for strings
3. Line length: 88 characters
4. Use type hints for all function parameters and return types
5. Write descriptive variable and function names
6. Add docstrings to all public functions and classes

## Versioning

This project uses **dynamic versioning** with `poetry-dynamic-versioning`. Install it
with:
```bash
poetry self add poetry-dynamic-versioning
```

### How Versioning Works

- Version is automatically determined from Git tags
- No need to manually update version numbers in files
- Versions follow [Semantic Versioning](https://semver.org/) (SemVer): `MAJOR.MINOR.PATCH`

### Creating Releases

1. Make sure all changes are committed and pushed
2. Create and push a git tag:
   ```bash
   # For a new patch version
   git tag v0.1.1
   git push origin v0.1.1

   # For a new minor version
   git tag v0.2.0
   git push origin v0.2.0

   # For a new major version
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. The version will be automatically set based on the tag

### Development Versions

Between releases, versions are automatically generated with commit information:
- Example: `0.1.1.dev123+g1a2b3c4`

## Publishing to PyPI

### Prerequisites

1. Have an account on [PyPI](https://pypi.org/)
2. Configure Poetry with your PyPI credentials:
   ```bash
   poetry config pypi-token.pypi your-pypi-token
   ```

### Publishing Process

1. **Ensure everything is ready**:
   - All tests pass: `poetry run pytest`
   - All commits have passed pre-commit hooks (automatic)
   - Documentation is up to date

2. **Create an empty commit** (this sets the version):
   ```bash
    git commit --allow-empty -m "release v1.2.3"
   ```

3. **Create a git tag** (this sets the version):
   ```bash
    git tag v1.2.3
    git push origin v1.2.3
   ```

4. **Build the package**:
   ```bash
   poetry build
   ```

4. **Publish to PyPI**:
   ```bash
   poetry publish
   ```

### Publishing to Test PyPI

For testing purposes, you can publish to Test PyPI first:

1. Configure Test PyPI:
   ```bash
   poetry config repositories.testpypi https://test.pypi.org/legacy/
   poetry config pypi-token.testpypi your-test-pypi-token
   ```

2. Publish to Test PyPI:
   ```bash
   poetry publish -r testpypi
   ```

## Project Structure

```
randex/
├── randex/                 # Main package
│   ├── __init__.py
│   └── exam.py            # Core classes and functions
├── scripts/               # CLI scripts
│   ├── exams.py          # Main exam generation script
│   ├── validate.py       # Question validation script
│   └── randex_download_examples.py
├── tests/                 # Test suite
│   ├── conftest.py       # Test fixtures and configuration
│   └── test_*.py         # Individual test modules
├── examples/              # Example questions and templates
│   ├── en/               # English examples
│   └── gr/               # Greek examples
├── pyproject.toml        # Project configuration
├── poetry.lock           # Locked dependencies
└── README.md             # Project documentation
```

### Key Files

- **`pyproject.toml`**: Project configuration, dependencies, build settings
- **`randex/exam.py`**: Main implementation with Question, Exam, Pool, and related classes
- **`tests/conftest.py`**: Shared test fixtures and configuration
- **`scripts/`**: Command-line interface implementations

## Git Workflow

### Branch Strategy

1. **main**: Stable branch, always ready for release
2. **feature branches**: For new features (`feature/feature-name`)
3. **bugfix branches**: For bug fixes (`bugfix/issue-description`)

### Commit Guidelines

1. Use clear, descriptive commit messages
2. Start with a verb in present tense ("Add", "Fix", "Update")
3. Keep the first line under 50 characters
4. Add detailed description if needed

Example:
```
Add support for multiple question formats

- Implement new YAML schema validation
- Add tests for various question formats
- Update documentation with examples
```

### Pull Request Process

1. Create a feature branch from main
2. Make your changes with tests and documentation
3. Run the test suite: `poetry run pytest`
4. Commit your changes (pre-commit hooks will run automatically)
5. Create a pull request with clear description
6. Address any review feedback
7. Merge after approval

## Getting Help

- Check existing [issues](https://github.com/arampatzis/randex/issues) and [pull requests](https://github.com/arampatzis/randex/pulls)
- Read the [README.md](README.md) for usage instructions
- Look at the test files for usage examples
- Check the docstrings in the code for detailed API documentation

## License

This project is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
Commercial use is prohibited without prior permission.
