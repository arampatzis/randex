# Test Suite for Randex

This directory contains comprehensive unit and integration tests for the Randex exam generation library.

## Test Structure

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`test_question.py`** - Tests for the `Question` class
- **`test_pool.py`** - Tests for the `Pool` class and utility functions
- **`test_question_set.py`** - Tests for the `QuestionSet` class
- **`test_exam_template.py`** - Tests for the `ExamTemplate` class
- **`test_exam.py`** - Tests for the `Exam` class
- **`test_exam_batch.py`** - Tests for the `ExamBatch` class
- **`test_scripts.py`** - Tests for the command-line scripts
- **`test_integration.py`** - End-to-end integration tests

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Files
```bash
pytest tests/test_question.py
pytest tests/test_integration.py
```

### Run Tests with Coverage
```bash
pytest --cov=randex --cov-report=html
```

### Run Tests by Category
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Verbose Output
```bash
pytest -v
```

## Test Coverage

The test suite covers:

### Core Classes
- ✅ `Question` - validation, shuffling, LaTeX output, string representation
- ✅ `Pool` - folder resolution, question loading, glob patterns
- ✅ `QuestionSet` - sampling strategies, size calculation, key handling
- ✅ `ExamTemplate` - YAML loading, validation, defaults
- ✅ `Exam` - validation, compilation, shuffling, serial numbers
- ✅ `ExamBatch` - batch creation, compilation, save/load functionality

### Utility Functions
- ✅ `is_glob_expression` - glob pattern detection

### Command Line Interface
- ✅ CLI argument parsing and validation
- ✅ Integration with core classes
- ✅ Error handling

### Integration Workflows
- ✅ End-to-end question loading → exam generation
- ✅ Per-folder sampling strategies
- ✅ Question and answer shuffling
- ✅ Batch save/load operations
- ✅ Error handling with invalid data

## Test Data and Fixtures

The test suite uses several fixtures for consistent test data:

- `sample_question_data` - Basic question dictionary
- `sample_question` - Single `Question` instance
- `sample_questions` - List of `Question` instances
- `sample_exam_template` - Basic `ExamTemplate` instance
- `temp_dir` - Temporary directory for file operations
- `sample_question_files` - Temporary YAML question files
- `sample_template_file` - Temporary template YAML file

## Mocking and Isolation

Tests use mocking where appropriate to:
- Isolate units under test
- Avoid external dependencies (filesystem, subprocess calls)
- Control randomness for deterministic testing
- Speed up test execution

## Edge Cases and Error Handling

The test suite includes comprehensive edge case testing:
- Invalid input validation
- Empty data sets
- File I/O errors
- YAML parsing errors
- Boundary conditions
- Type coercion and validation

## Performance Considerations

Some tests are marked as "slow" and can be skipped for faster development cycles:
```bash
pytest -m "not slow"
```

Integration tests may take longer as they test complete workflows including file I/O operations.
