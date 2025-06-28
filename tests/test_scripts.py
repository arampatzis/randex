"""Tests for the command-line scripts."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from scripts.batch import main as exams_main


class TestExamsScript:
    """Test the exams CLI script."""

    def test_exams_help(self) -> None:
        """Test that help option works."""
        runner = CliRunner()
        result = runner.invoke(exams_main, ["--help"])

        assert result.exit_code == 0
        assert "Create a batch of exams" in result.output
        assert "--batch-size" in result.output
        assert "--number_of_questions" in result.output

    def test_exams_missing_required_args(self) -> None:
        """Test script with missing required arguments."""
        runner = CliRunner()
        result = runner.invoke(exams_main, [])

        # Should fail due to missing arguments
        assert result.exit_code != 0

    @patch("scripts.exams.Pool")
    @patch("scripts.exams.ExamBatch")
    @patch("scripts.exams.QuestionSet")
    def test_exams_basic_run(
        self,
        mock_question_set_class: MagicMock,
        mock_batch_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """Test basic script execution."""
        # Mock the Pool and ExamBatch classes
        mock_pool = MagicMock()
        # Create mock questions for the pool
        from randex.exam import Question

        mock_questions = [
            Question(question="Test 1?", answers=["a", "b", "c", "d"], right_answer=0),
            Question(question="Test 2?", answers=["w", "x", "y", "z"], right_answer=1),
            Question(question="Test 3?", answers=["1", "2", "3", "4"], right_answer=2),
        ]
        mock_pool.questions = {"folder1": mock_questions}
        mock_pool_class.return_value = mock_pool

        mock_batch = MagicMock()
        mock_batch_class.return_value = mock_batch

        mock_question_set = MagicMock()
        mock_question_set_class.return_value = mock_question_set

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a test folder
            test_folder = Path("test_folder")
            test_folder.mkdir()

            result = runner.invoke(
                exams_main,
                [
                    str(test_folder),
                    "-t",
                    str(sample_template_file),
                    "-b",
                    "2",
                    "-n",
                    "3",
                ],
            )

            # Should succeed
            assert result.exit_code == 0

            # Should have called the expected methods
            assert mock_pool_class.called
            assert mock_batch_class.called
            assert mock_batch.make_batch.called
            assert mock_batch.compile.called

    def test_exams_with_batch_size(self, sample_template_file: Path) -> None:
        """Test script with different batch sizes."""
        with (
            patch("scripts.exams.Pool") as mock_pool_class,
            patch("scripts.exams.ExamBatch") as mock_batch_class,
            patch("scripts.exams.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?", answers=["a", "b", "c", "d"], right_answer=0
                ),
                Question(
                    question="Test 2?", answers=["w", "x", "y", "z"], right_answer=1
                ),
            ]
            mock_pool.questions = {"folder1": mock_questions}
            mock_pool_class.return_value = mock_pool

            mock_batch = MagicMock()
            mock_batch_class.return_value = mock_batch

            mock_question_set = MagicMock()
            mock_question_set_class.return_value = mock_question_set

            runner = CliRunner()
            with runner.isolated_filesystem():
                test_folder = Path("test_folder")
                test_folder.mkdir()

                result = runner.invoke(
                    exams_main,
                    [
                        str(test_folder),
                        "-t",
                        str(sample_template_file),
                        "-b",
                        "5",  # Batch size 5
                        "-n",
                        "2",
                    ],
                )

                assert result.exit_code == 0

                # Check that batch was created with correct size
                call_args = mock_batch_class.call_args
                assert call_args[1]["N"] == 5

    def test_exams_multiple_question_counts(self, sample_template_file: Path) -> None:
        """Test script with multiple -n flags (per-folder counts)."""
        with (
            patch("scripts.exams.Pool") as mock_pool_class,
            patch("scripts.exams.ExamBatch") as mock_batch_class,
            patch("scripts.exams.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for both folders
            from randex.exam import Question

            mock_questions_1 = [
                Question(
                    question="Test 1?", answers=["a", "b", "c", "d"], right_answer=0
                ),
                Question(
                    question="Test 2?", answers=["w", "x", "y", "z"], right_answer=1
                ),
            ]
            mock_questions_2 = [
                Question(
                    question="Test 3?", answers=["1", "2", "3", "4"], right_answer=2
                ),
                Question(
                    question="Test 4?", answers=["p", "q", "r", "s"], right_answer=3
                ),
                Question(
                    question="Test 5?", answers=["i", "j", "k", "l"], right_answer=0
                ),
            ]
            mock_pool.questions = {
                "folder1": mock_questions_1,
                "folder2": mock_questions_2,
            }
            mock_pool_class.return_value = mock_pool

            mock_batch = MagicMock()
            mock_batch_class.return_value = mock_batch

            mock_question_set = MagicMock()
            mock_question_set_class.return_value = mock_question_set

            runner = CliRunner()
            with runner.isolated_filesystem():
                test_folder = Path("test_folder")
                test_folder.mkdir()

                result = runner.invoke(
                    exams_main,
                    [
                        str(test_folder),
                        "-t",
                        str(sample_template_file),
                        "-n",
                        "2",
                        "-n",
                        "3",  # Multiple -n flags
                    ],
                )

                assert result.exit_code == 0

                # Check that correct question counts were passed
                call_args = mock_batch_class.call_args
                assert call_args[1]["n"] == (2, 3)

    def test_exams_with_output_folder(self, sample_template_file: Path) -> None:
        """Test script with custom output folder."""
        with (
            patch("scripts.exams.Pool") as mock_pool_class,
            patch("scripts.exams.ExamBatch") as mock_batch_class,
            patch("scripts.exams.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?", answers=["a", "b", "c", "d"], right_answer=0
                ),
                Question(
                    question="Test 2?", answers=["w", "x", "y", "z"], right_answer=1
                ),
            ]
            mock_pool.questions = {"folder1": mock_questions}
            mock_pool_class.return_value = mock_pool

            mock_batch = MagicMock()
            mock_batch_class.return_value = mock_batch

            mock_question_set = MagicMock()
            mock_question_set_class.return_value = mock_question_set

            runner = CliRunner()
            with runner.isolated_filesystem():
                test_folder = Path("test_folder")
                test_folder.mkdir()

                result = runner.invoke(
                    exams_main,
                    [
                        str(test_folder),
                        "-t",
                        str(sample_template_file),
                        "-o",
                        "custom_output",
                        "-n",
                        "2",
                    ],
                )

                assert result.exit_code == 0

                # Should have used custom output folder
                compile_call_args = mock_batch.compile.call_args
                assert "custom_output" in str(compile_call_args[1]["path"])

    def test_exams_overwrite_existing_folder(self, sample_template_file: Path) -> None:
        """Test script with --overwrite flag."""
        with (
            patch("scripts.exams.Pool") as mock_pool_class,
            patch("scripts.exams.ExamBatch") as mock_batch_class,
            patch("scripts.exams.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?", answers=["a", "b", "c", "d"], right_answer=0
                ),
                Question(
                    question="Test 2?", answers=["w", "x", "y", "z"], right_answer=1
                ),
            ]
            mock_pool.questions = {"folder1": mock_questions}
            mock_pool_class.return_value = mock_pool

            mock_batch = MagicMock()
            mock_batch_class.return_value = mock_batch

            mock_question_set = MagicMock()
            mock_question_set_class.return_value = mock_question_set

            runner = CliRunner()
            with runner.isolated_filesystem():
                test_folder = Path("test_folder")
                test_folder.mkdir()

                # Create existing output folder
                output_folder = Path("existing_output")
                output_folder.mkdir()

                # Without --overwrite should fail
                result = runner.invoke(
                    exams_main,
                    [
                        str(test_folder),
                        "-t",
                        str(sample_template_file),
                        "-o",
                        str(output_folder),
                        "-n",
                        "2",
                    ],
                )
                assert result.exit_code != 0
                assert "already exists" in result.output

                # With --overwrite should succeed
                result = runner.invoke(
                    exams_main,
                    [
                        str(test_folder),
                        "-t",
                        str(sample_template_file),
                        "-o",
                        str(output_folder),
                        "--overwrite",
                        "-n",
                        "2",
                    ],
                )
                assert result.exit_code == 0

    def test_exams_clean_flag(self, sample_template_file: Path) -> None:
        """Test script with --clean flag."""
        with (
            patch("scripts.exams.Pool") as mock_pool_class,
            patch("scripts.exams.ExamBatch") as mock_batch_class,
            patch("scripts.exams.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?", answers=["a", "b", "c", "d"], right_answer=0
                ),
                Question(
                    question="Test 2?", answers=["w", "x", "y", "z"], right_answer=1
                ),
            ]
            mock_pool.questions = {"folder1": mock_questions}
            mock_pool_class.return_value = mock_pool

            mock_batch = MagicMock()
            mock_batch_class.return_value = mock_batch

            mock_question_set = MagicMock()
            mock_question_set_class.return_value = mock_question_set

            runner = CliRunner()
            with runner.isolated_filesystem():
                test_folder = Path("test_folder")
                test_folder.mkdir()

                result = runner.invoke(
                    exams_main,
                    [
                        str(test_folder),
                        "-t",
                        str(sample_template_file),
                        "--clean",
                        "-n",
                        "2",
                    ],
                )

                assert result.exit_code == 0

                # Should have called compile with clean=True
                compile_calls = mock_batch.compile.call_args_list
                assert any(call[1].get("clean", False) for call in compile_calls)

    def test_exams_nonexistent_template(self) -> None:
        """Test script with non-existent template file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            result = runner.invoke(
                exams_main,
                [str(test_folder), "-t", "nonexistent_template.yaml", "-n", "2"],
            )

            # Should fail due to missing template file
            assert result.exit_code != 0


class TestValidateScript:
    """Test the validate CLI script."""

    def test_validate_script_import(self) -> None:
        """Test that validate script can be imported."""
        try:
            from scripts.validate import main as validate_main

            assert callable(validate_main)
        except ImportError:
            pytest.skip("Validate script not available")

    def test_validate_help(self) -> None:
        """Test validate script help."""
        try:
            from scripts.validate import main as validate_main

            runner = CliRunner()
            result = runner.invoke(validate_main, ["--help"])

            assert result.exit_code == 0
            assert "help" in result.output.lower()
        except ImportError:
            pytest.skip("Validate script not available")
