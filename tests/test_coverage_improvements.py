"""Tests to improve coverage for uncovered edge cases and error paths."""

import subprocess
from contextlib import suppress
from unittest.mock import MagicMock, patch

import pytest
import yaml

from randex.exam import Exam, ExamBatch, ExamTemplate, Pool, QuestionSet


class TestPoolEdgeCases:
    """Test edge cases for Pool class to improve coverage."""

    def test_pool_glob_pattern_no_matches(self, temp_dir):
        """Test Pool with glob pattern that matches no folders."""
        # Create a pattern that won't match anything
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)  # Change to temp directory so glob can work

            # This pattern has * so it will be treated as glob, but won't match anything
            pool = Pool(folder="nonexistent_*/pattern")
            # Access a property that triggers resolve_folder_input
            with pytest.raises(
                ValueError, match="No folders found matching the pattern"
            ):
                _ = pool.questions
        finally:
            os.chdir(original_cwd)  # Always restore original directory

    def test_pool_print_questions_method(self, temp_dir):
        """Test Pool.print_questions method."""
        # Create a folder with questions
        folder = temp_dir / "test_folder"
        folder.mkdir()

        question_file = folder / "q1.yaml"
        question_data = {
            "question": "What is 2+2?",
            "answers": ["3", "4", "5"],
            "right_answer": 1,
        }
        with open(question_file, "w") as f:
            yaml.dump(question_data, f)

        pool = Pool(folder=folder)

        # Test the print_questions method
        with patch("randex.cli.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            pool.print_questions()

            # Verify that logger.info was called
            assert mock_logger.info.called
            # Should have called with folder name and question details
            calls = mock_logger.info.call_args_list
            assert any("test_folder" in str(call) for call in calls)
            assert any("What is 2+2?" in str(call) for call in calls)

    def test_pool_print_questions_empty_folders(self, temp_dir):
        """Test Pool.print_questions with empty folders (should continue)."""
        # Create folder with valid questions to actually test the print functionality
        folder = temp_dir / "test_folder"
        folder.mkdir()

        # Create a valid question to ensure print_questions actually runs
        question_file = folder / "q1.yaml"
        question_data = {
            "question": "What is 2+2?",
            "answers": ["3", "4", "5"],
            "right_answer": 1,
        }
        with open(question_file, "w") as f:
            yaml.dump(question_data, f)

        # Create an empty subfolder
        empty_folder = folder / "empty_subfolder"
        empty_folder.mkdir()

        pool = Pool(folder=folder)

        with patch("randex.cli.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # This should not raise an error, just continue
            pool.print_questions()

            # Should have logging from the valid questions
            assert mock_logger.info.called


class TestQuestionSetEdgeCases:
    """Test edge cases for QuestionSet to improve coverage."""

    def test_questionset_sample_invalid_type(self, sample_questions):
        """
        Test QuestionSet.sample.

        With invalid type to hit the unreachable TypeError.
        """
        from collections import OrderedDict

        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        # This should hit the unreachable TypeError case by bypassing type hints
        # Use a type that bypasses the type hints but fails at runtime
        with pytest.raises(
            TypeError, match="n must be an int, list\\[int\\], or tuple\\[int\\]"
        ):
            question_set.sample("invalid_string_type")  # type: ignore[arg-type]


class TestExamTemplateEdgeCases:
    """Test edge cases for ExamTemplate to improve coverage."""

    def test_exam_template_load_nonexistent_file(self, temp_dir):
        """Test ExamTemplate.load with nonexistent file."""
        nonexistent_file = temp_dir / "nonexistent.yaml"

        with patch("randex.exam.logger") as mock_logger:
            template = ExamTemplate.load(nonexistent_file)

            # Should return default template
            assert isinstance(template, ExamTemplate)
            # Should log a warning
            mock_logger.warning.assert_called_once()
            assert "does not exist" in str(mock_logger.warning.call_args)


class TestExamGradingEdgeCases:
    """Test edge cases for Exam.grade method to improve coverage."""

    def test_exam_grade_negative_score_validation(
        self, sample_questions, sample_exam_template
    ):
        """Test Exam.grade with invalid negative_score values."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:2],
        )

        # Test negative score < 0
        with pytest.raises(ValueError, match="Negative score must be between 0 and 1"):
            exam.grade([0, 1], negative_score=-0.1)

        # Test negative score > 1
        with pytest.raises(ValueError, match="Negative score must be between 0 and 1"):
            exam.grade([0, 1], negative_score=1.1)

    def test_exam_grade_wrong_answer_count(
        self, sample_questions, sample_exam_template
    ):
        """Test Exam.grade with wrong number of answers."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:2],
        )

        # Too few answers
        with pytest.raises(ValueError, match="Expected 2 answers, but got 1"):
            exam.grade([0])

        # Too many answers
        with pytest.raises(ValueError, match="Expected 2 answers, but got 3"):
            exam.grade([0, 1, 2])

    def test_exam_grade_with_negative_score(
        self, sample_questions, sample_exam_template
    ):
        """Test Exam.grade with custom negative_score."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:2],
        )

        # All wrong answers with custom negative score
        score = exam.grade([1, 0], negative_score=0.5)  # Both wrong
        expected = -1.0  # -0.5 for each wrong answer
        assert score == expected

        # Mix of right, wrong, and None
        score = exam.grade(
            [1, None], negative_score=0.2
        )  # First wrong, second unanswered
        expected = -0.2  # -0.2 for wrong, 0 for unanswered
        assert score == expected

    def test_exam_grade_default_negative_scoring(
        self, sample_questions, sample_exam_template
    ):
        """Test Exam.grade with default negative scoring formula."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],  # Use question with 4 answers
        )

        # Wrong answer with default scoring: -1/(num_answers-1)
        score = exam.grade([1])  # Wrong answer (right is 0)
        expected = -1 / (4 - 1)  # -1/3 ≈ -0.3, rounded to -0.3
        assert score == round(expected, 1)


class TestExamCompilationEdgeCases:
    """Test edge cases for Exam.compile method to improve coverage."""

    def test_exam_compile_timeout_exception(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test Exam.compile with subprocess timeout."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],
        )

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("latexmk", 3600)

            with pytest.raises(
                RuntimeError, match="Compilation timed out after 5 minutes"
            ):
                exam.compile(temp_dir)

    def test_exam_compile_cleanup_timeout(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test Exam.compile with cleanup timeout."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],
        )

        with patch("subprocess.run") as mock_run:
            # First call (compilation) succeeds, second call (cleanup) times out
            mock_run.side_effect = [
                MagicMock(returncode=0),  # Compilation success
                subprocess.TimeoutExpired("latexmk", 600),  # Cleanup timeout
            ]

            with pytest.raises(
                RuntimeError, match="Cleanup timed out after 10 minutes"
            ):
                exam.compile(temp_dir, clean=True)

    def test_exam_compile_cleanup_warning_path(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test Exam.compile cleanup timeout warning path."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],
        )

        with (
            patch("subprocess.run") as mock_run,
            patch("randex.exam.logger") as mock_logger,
        ):
            # First call (compilation) succeeds, second call (cleanup) times out
            mock_run.side_effect = [
                MagicMock(returncode=0),  # Compilation success
                subprocess.TimeoutExpired("latexmk", 600),  # Cleanup timeout
            ]

            with suppress(RuntimeError):
                exam.compile(temp_dir, clean=True)

            # Should have logged a warning before raising the error
            mock_logger.warning.assert_called_with("Cleanup timed out")


class TestExamBatchErrorHandling:
    """Test edge cases for ExamBatch error handling to improve coverage."""

    def test_exam_batch_make_batch_exception_handling(
        self, sample_questions, sample_exam_template
    ):
        """Test ExamBatch.make_batch with exception during exam creation."""
        from collections import OrderedDict

        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        # Mock the questions_set.sample method using the module level
        with (
            patch(
                "randex.exam.QuestionSet.sample", side_effect=Exception("Sample failed")
            ),
            pytest.raises(RuntimeError, match="Failed to create exam 0"),
        ):
            batch.make_batch()

    def test_exam_batch_compile_single_exam_validation_error(self, temp_dir):
        """Test ExamBatch._compile_single_exam with ValidationError."""
        # Create invalid exam data that will cause ValidationError
        invalid_exam_data = {
            "sn": "0",
            "questions": [],  # Empty questions will cause ValidationError
            "exam_template": {},
        }

        exam_dir = temp_dir / "exam_0"

        sn, success, error_msg = ExamBatch._compile_single_exam(
            invalid_exam_data, exam_dir, clean=False
        )

        assert sn == "0"
        assert success is False
        assert error_msg  # Should contain error message

    def test_exam_batch_compile_single_exam_subprocess_error(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test ExamBatch._compile_single_exam with subprocess error."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],
            sn="0",
        )

        exam_data = exam.model_dump(mode="json")
        exam_dir = temp_dir / "exam_0"

        with patch(
            "subprocess.run",
            side_effect=subprocess.SubprocessError("Subprocess failed"),
        ):
            sn, success, error_msg = ExamBatch._compile_single_exam(
                exam_data, exam_dir, clean=False
            )

            assert sn == "0"
            assert success is False
            assert "Subprocess failed" in error_msg

    def test_exam_batch_compile_single_exam_os_error(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test ExamBatch._compile_single_exam with OSError."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],
            sn="0",
        )

        exam_data = exam.model_dump(mode="json")
        exam_dir = temp_dir / "exam_0"

        with patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")):
            sn, success, error_msg = ExamBatch._compile_single_exam(
                exam_data, exam_dir, clean=False
            )

            assert sn == "0"
            assert success is False
            assert "Permission denied" in error_msg

    def test_exam_batch_parallel_compilation_exception_handling(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test ExamBatch parallel compilation with exception in future."""
        import os
        from collections import OrderedDict

        # Ensure we're in a valid directory for multiprocessing
        original_cwd = os.getcwd()

        try:
            questions_dict = OrderedDict({"folder1": sample_questions})
            question_set = QuestionSet(questions=questions_dict)

            batch = ExamBatch(
                N=2,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=1,
            )

            batch.make_batch()

            with patch(
                "randex.exam.ExamBatch._compile_single_exam",
                side_effect=Exception("Compilation failed"),
            ):
                pdf_files, failed = batch._run_parallel_compilation(
                    temp_dir, clean=False
                )

                # Should handle the exception and add to failed list
                assert len(failed) >= 1
                assert len(pdf_files) == 0
        finally:
            os.chdir(original_cwd)

    def test_exam_batch_compile_no_exams_error(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test ExamBatch.compile with no exams made."""
        from collections import OrderedDict

        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=1,
        )

        # Don't call make_batch()
        with pytest.raises(
            RuntimeError, match="No exams to compile. Call make_batch\\(\\) first."
        ):
            batch.compile(temp_dir)


class TestCLIScripts:
    """Test CLI scripts for additional coverage."""

    def test_grade_script_functionality(self, temp_dir):
        """Test the grade script functionality."""
        # Create a simple batch file and answers CSV
        from randex.exam import ExamBatch, ExamTemplate, QuestionSet

        # Create sample questions
        folder = temp_dir / "questions"
        folder.mkdir()

        question_file = folder / "q1.yaml"
        question_data = {
            "question": "Test question?",
            "answers": ["A", "B", "C"],
            "right_answer": 1,
        }
        with open(question_file, "w") as f:
            yaml.dump(question_data, f)

        # Create a batch
        pool = Pool(folder=folder)
        question_set = QuestionSet(questions=pool.questions)
        template = ExamTemplate()

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=template,
            n=1,
        )
        batch.make_batch()

        # Save batch
        batch_file = temp_dir / "batch.yaml"
        batch.save(batch_file)

        # Create answers CSV
        answers_file = temp_dir / "answers.csv"
        with open(answers_file, "w") as f:
            f.write("sn,q1\n")
            f.write("0,1\n")  # Correct answer
            f.write("1,0\n")  # Wrong answer

        # Test the grade script
        from cli.grade import main as grade_main

        # Should not raise an exception
        grade_main(batch_file, answers_file)

    def test_random_answers_script_functionality(self, temp_dir):
        """Test the random_answers script functionality."""
        from randex.exam import ExamBatch, ExamTemplate, QuestionSet

        # Create sample questions
        folder = temp_dir / "questions"
        folder.mkdir()

        question_file = folder / "q1.yaml"
        question_data = {
            "question": "Test question?",
            "answers": ["A", "B", "C"],
            "right_answer": 1,
        }
        with open(question_file, "w") as f:
            yaml.dump(question_data, f)

        # Create a batch
        pool = Pool(folder=folder)
        question_set = QuestionSet(questions=pool.questions)
        template = ExamTemplate()

        batch = ExamBatch(
            N=3,  # Test different cases: 0, 1, 2, others
            questions_set=question_set,
            exam_template=template,
            n=1,
        )
        batch.make_batch()

        # Save batch
        batch_file = temp_dir / "batch.yaml"
        batch.save(batch_file)

        # Test the random_answers script
        from cli.random_answers import main as random_answers_main

        # Should not raise an exception and create a CSV file
        random_answers_main(batch_file)

        # Check that the CSV file was created
        csv_file = temp_dir / "random_answers.csv"
        assert csv_file.exists()

        # Read and verify CSV content
        import csv

        with open(csv_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3  # Should have 3 exams
            assert "sn" in rows[0]
            assert "q1" in rows[0]
