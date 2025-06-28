"""Tests for the ExamBatch class."""

from collections import OrderedDict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from pydantic import ValidationError

from randex.exam import ExamBatch, QuestionSet


class TestExamBatchValidation:
    """Test ExamBatch validation."""

    def test_create_valid_batch(self, sample_questions, sample_exam_template):
        """Test creating a valid exam batch."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=3,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        assert batch.N == 3
        assert batch.n == 2
        assert len(batch.exams) == 0  # Not made yet

    def test_validate_N_positive(self, sample_questions, sample_exam_template): # noqa: N802
        """Test that N must be positive."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        with pytest.raises(ValidationError, match="must be a positive integer"):
            ExamBatch(
                N=0,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=2,
            )

        with pytest.raises(ValidationError, match="must be a positive integer"):
            ExamBatch(
                N=-1,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=2,
            )

    def test_validate_n_type_conversion(self, sample_questions, sample_exam_template):
        """Test n type validation and conversion."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        # Single int should work
        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )
        assert batch.n == 2

        # List should work
        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=[2],
        )
        assert batch.n == [2]

        # Tuple should work
        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=(2,),
        )
        assert batch.n == (2,)

    def test_validate_question_availability(
        self, sample_questions, sample_exam_template
    ):
        """Test question availability validation."""
        questions_dict = OrderedDict(
            {"folder1": sample_questions[:1]}
        )  # Only 1 question
        question_set = QuestionSet(questions=questions_dict)

        # Should fail if trying to sample more questions than available
        with pytest.raises(
            ValidationError, match="Requested .* questions, but only .* available"
        ):
            ExamBatch(
                N=2,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=5,  # More than available
            )


class TestExamBatchMethods:
    """Test ExamBatch methods."""

    def test_make_batch(self, sample_questions, sample_exam_template):
        """Test batch creation."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()

        # Should have created 2 exams
        assert len(batch.exams) == 2

        # Each exam should have 2 questions
        for exam in batch.exams:
            assert len(exam.questions) == 2
            assert exam.exam_template == sample_exam_template

    def test_make_batch_with_per_folder_sampling(
        self, sample_questions, sample_exam_template
    ):
        """Test batch creation with per-folder sampling."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],
                "folder2": sample_questions[2:],
            }
        )
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=[1, 1],  # 1 from each folder
        )

        batch.make_batch()

        # Should have created 2 exams
        assert len(batch.exams) == 2

        # Each exam should have 2 questions (1 from each folder)
        for exam in batch.exams:
            assert len(exam.questions) == 2

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_compile_batch(
        self, mock_exists, mock_run, sample_questions, sample_exam_template, temp_dir
    ):
        """Test batch compilation."""
        mock_run.return_value = MagicMock(returncode=0)
        # Mock PDF file existence to return True
        mock_exists.return_value = True

        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()
        batch.compile(path=temp_dir)

        # Should call subprocess for each exam
        assert mock_run.call_count >= 2

    def test_save_batch(self, sample_questions, sample_exam_template, temp_dir):
        """Test saving batch to YAML file."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()

        save_path = temp_dir / "batch.yaml"
        batch.save(save_path)

        # File should exist
        assert save_path.exists()

        # Should be valid YAML
        with open(save_path) as f:
            data = yaml.safe_load(f)

        assert isinstance(data, dict)
        assert "N" in data
        assert "exams" in data

    def test_load_batch(self, sample_questions, sample_exam_template, temp_dir):
        """Test loading batch from YAML file."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        # Create and save a batch
        original_batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )
        original_batch.make_batch()

        save_path = temp_dir / "batch.yaml"
        original_batch.save(save_path)

        # Load the batch
        loaded_batch = ExamBatch.load(save_path)

        assert loaded_batch.N == original_batch.N
        assert len(loaded_batch.exams) == len(original_batch.exams)


class TestExamBatchEdgeCases:
    """Test edge cases for ExamBatch."""

    def test_batch_with_show_answers(self, sample_questions, sample_exam_template):
        """Test batch with show_answers=True."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
            show_answers=True,
        )

        batch.make_batch()

        # All exams should have show_answers=True
        for exam in batch.exams:
            assert exam.show_answers is True

    def test_batch_with_single_exam(self, sample_questions, sample_exam_template):
        """Test batch with single exam."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=1,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()

        assert len(batch.exams) == 1
        assert len(batch.exams[0].questions) == 2

    def test_batch_serial_numbers(self, sample_questions, sample_exam_template):
        """Test that exams get proper serial numbers."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=3,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()

        # Should have sequential serial numbers (0-indexed, padded to width of N)
        serial_numbers = [exam.sn for exam in batch.exams]
        expected = ["0", "1", "2"]  # For N=3, serial_width=1, so no padding needed
        assert serial_numbers == expected

    def test_batch_serial_numbers_with_padding(
        self, sample_questions, sample_exam_template
    ):
        """Test serial number zero-padding for larger batches."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        # Create a batch of 12 exams to test padding
        batch = ExamBatch(
            N=12,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=1,  # 1 question per exam
        )

        batch.make_batch()

        # For N=12, serial_width=2, so numbers should be zero-padded
        serial_numbers = [exam.sn for exam in batch.exams]
        expected = [f"{i:02d}" for i in range(12)]  # ["00", "01", "02", ..., "11"]
        assert serial_numbers == expected
        assert all(len(sn) == 2 for sn in serial_numbers)

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            ExamBatch.load("/nonexistent/path.yaml")

    def test_save_to_string_path(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test saving with string path."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=1,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()

        save_path = str(temp_dir / "batch.yaml")
        batch.save(save_path)

        # File should exist
        assert Path(save_path).exists()

    def test_compile_with_clean(self, sample_questions, sample_exam_template, temp_dir):
        """Test compilation with clean flag."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True  # Mock PDF file existence

            questions_dict = OrderedDict({"folder1": sample_questions})
            question_set = QuestionSet(questions=questions_dict)

            batch = ExamBatch(
                N=1,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=2,
            )

            batch.make_batch()
            batch.compile(path=temp_dir, clean=True)

            # Should call subprocess (compile + potential clean commands)
            assert mock_run.called

    def test_batch_with_empty_question_set(self, sample_exam_template):
        """Test batch creation with empty question set."""
        question_set = QuestionSet(questions=OrderedDict())

        with pytest.raises(ValidationError):
            ExamBatch(
                N=1,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=1,  # Cannot sample from empty set
            )
