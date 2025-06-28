"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from randex.exam import ExamTemplate, Question


@pytest.fixture
def sample_question_data() -> dict[str, Any]:
    """Sample question data for testing."""
    return {
        "question": "What is $1+1$?",
        "answers": ["0", "1", "2", "3"],
        "right_answer": 2,
    }


@pytest.fixture
def sample_question(sample_question_data: dict[str, Any]) -> Question:
    """Sample Question instance for testing."""
    return Question(**sample_question_data)


@pytest.fixture
def sample_questions() -> list[Question]:
    """Multiple sample questions for testing."""
    return [
        Question(
            question="What is $1+1$?",
            answers=["0", "1", "2", "3"],
            right_answer=2,
        ),
        Question(
            question="What is $2+2$?",
            answers=["2", "3", "4", "5"],
            right_answer=2,
        ),
        Question(
            question="What is $3+3$?",
            answers=["4", "5", "6", "7"],
            right_answer=2,
        ),
    ]


@pytest.fixture
def sample_exam_template() -> ExamTemplate:
    """Sample ExamTemplate for testing."""
    return ExamTemplate(
        documentclass="\\documentclass[11pt]{exam}\n\n",
        lhead="Test Exam",
        chead="Page \\thepage",
    )


@pytest.fixture
def temp_dir():
    """Temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_question_files(temp_dir: Path) -> Path:
    """Create temporary YAML question files for testing."""
    # Create folder structure
    folder1 = temp_dir / "folder1"
    folder2 = temp_dir / "folder2"
    folder1.mkdir()
    folder2.mkdir()

    # Sample questions for folder1
    q1_data = {
        "question": "What is $1+1$?",
        "answers": ["0", "1", "2", "3"],
        "right_answer": 2,
    }
    q2_data = {
        "question": "What is $2+2$?",
        "answers": ["2", "3", "4", "5"],
        "right_answer": 2,
    }

    # Sample questions for folder2
    q3_data = {
        "question": "What is $3+3$?",
        "answers": ["4", "5", "6", "7"],
        "right_answer": 2,
    }

    # Write YAML files
    with open(folder1 / "q1.yaml", "w") as f:
        yaml.dump(q1_data, f)
    with open(folder1 / "q2.yaml", "w") as f:
        yaml.dump(q2_data, f)
    with open(folder2 / "q3.yaml", "w") as f:
        yaml.dump(q3_data, f)

    return temp_dir


@pytest.fixture
def sample_template_file(temp_dir: Path) -> Path:
    """Create a temporary template YAML file for testing."""
    template_data = {
        "documentclass": "\\documentclass[11pt]{exam}\n\n",
        "prebegin": "\\usepackage{amsmath}\n",
        "lhead": "Test Exam",
        "chead": "Page \\thepage",
    }

    template_file = temp_dir / "template.yaml"
    with open(template_file, "w") as f:
        yaml.dump(template_data, f)

    return template_file
