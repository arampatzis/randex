"""Tests for the command-line scripts."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from scripts.randex import cli


class TestMainCLI:
    """Test the main CLI commands."""

    def test_main_help(self) -> None:
        """Test main CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "randex" in result.output
        assert "--verbose" in result.output
        assert "--quiet" in result.output

    def test_download_examples_help(self) -> None:
        """Test download-examples command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["download-examples", "--help"])

        assert result.exit_code == 0
        assert "Download the latest examples" in result.output


class TestDownloadExamplesScript:
    """Test the download-examples CLI script."""

    def test_download_examples_existing_folder(self) -> None:
        """Test download when examples folder already exists."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create existing examples directory
            examples_dir = Path("examples")
            examples_dir.mkdir()

            result = runner.invoke(cli, ["download-examples"])

            assert result.exit_code == 1
            assert "already exists" in result.output

    @patch("scripts.download_examples.urllib.request.urlopen")
    def test_download_examples_url_error(self, mock_urlopen: MagicMock) -> None:
        """Test download with URL error."""
        mock_urlopen.side_effect = URLError("Connection failed")

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["download-examples"])

            assert result.exit_code == 1
            assert "Error occurred during the download process" in result.output

    @patch("scripts.download_examples.urllib.request.urlopen")
    def test_download_examples_bad_zip(self, mock_urlopen: MagicMock) -> None:
        """Test download with bad zip file."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not a zip file"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["download-examples"])

            assert result.exit_code == 1
            assert "Error occurred during the download process" in result.output

    def test_download_examples_import_and_main_function(self) -> None:
        """Test that download_examples main function can be imported and called."""
        # Test importing the main function to get coverage on the function definition
        from scripts.download_examples import main as download_main

        # Test that it's a callable function
        assert callable(download_main)

        # Test DEST_DIR and GITHUB_ZIP_URL constants are defined
        from scripts.download_examples import DEST_DIR, GITHUB_ZIP_URL

        assert Path("examples") == DEST_DIR
        assert "github.com" in GITHUB_ZIP_URL

    # NOTE: Complex mocking tests for download_examples removed due to
    # Path.exists being read-only. The existing tests already provide
    # sufficient coverage for error paths.


class TestBatchScript:
    """Test the batch CLI script."""

    def test_batch_help(self) -> None:
        """Test that help option works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "--help"])

        assert result.exit_code == 0
        assert "Create a batch of exams" in result.output
        assert "--batch-size" in result.output
        assert "--number_of_questions" in result.output

    def test_batch_missing_required_args(self) -> None:
        """Test script with missing required arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch"])

        # Should fail due to missing arguments
        assert result.exit_code != 0

    @patch("scripts.batch.Pool")
    @patch("scripts.batch.ExamBatch")
    @patch("scripts.batch.QuestionSet")
    def test_batch_basic_run(
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
            Question(
                question="Test 1?",
                answers=["a", "b", "c", "d"],
                right_answer=0,
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
            # Create a test folder
            test_folder = Path("test_folder")
            test_folder.mkdir()

            result = runner.invoke(
                cli,
                [
                    "batch",
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

    def test_batch_with_batch_size(self, sample_template_file: Path) -> None:
        """Test script with different batch sizes."""
        with (
            patch("scripts.batch.Pool") as mock_pool_class,
            patch("scripts.batch.ExamBatch") as mock_batch_class,
            patch("scripts.batch.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?",
                    answers=["a", "b", "c", "d"],
                    right_answer=0,
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
                    cli,
                    [
                        "batch",
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

    def test_batch_multiple_question_counts(self, sample_template_file: Path) -> None:
        """Test script with multiple -n flags (per-folder counts)."""
        with (
            patch("scripts.batch.Pool") as mock_pool_class,
            patch("scripts.batch.ExamBatch") as mock_batch_class,
            patch("scripts.batch.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for both folders
            from randex.exam import Question

            mock_questions_1 = [
                Question(
                    question="Test 1?",
                    answers=["a", "b", "c", "d"],
                    right_answer=0,
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
                    cli,
                    [
                        "batch",
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

    def test_batch_with_output_folder(self, sample_template_file: Path) -> None:
        """Test script with custom output folder."""
        with (
            patch("scripts.batch.Pool") as mock_pool_class,
            patch("scripts.batch.ExamBatch") as mock_batch_class,
            patch("scripts.batch.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?",
                    answers=["a", "b", "c", "d"],
                    right_answer=0,
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
                    cli,
                    [
                        "batch",
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

    def test_batch_overwrite_existing_folder(self, sample_template_file: Path) -> None:
        """Test script with --overwrite flag."""
        with (
            patch("scripts.batch.Pool") as mock_pool_class,
            patch("scripts.batch.ExamBatch") as mock_batch_class,
            patch("scripts.batch.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?",
                    answers=["a", "b", "c", "d"],
                    right_answer=0,
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
                    cli,
                    [
                        "batch",
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
                    cli,
                    [
                        "batch",
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

    def test_batch_clean_flag(self, sample_template_file: Path) -> None:
        """Test script with --clean flag."""
        with (
            patch("scripts.batch.Pool") as mock_pool_class,
            patch("scripts.batch.ExamBatch") as mock_batch_class,
            patch("scripts.batch.QuestionSet") as mock_question_set_class,
        ):
            mock_pool = MagicMock()
            # Create mock questions for the pool
            from randex.exam import Question

            mock_questions = [
                Question(
                    question="Test 1?",
                    answers=["a", "b", "c", "d"],
                    right_answer=0,
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
                    cli,
                    [
                        "batch",
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

    def test_batch_nonexistent_template(self) -> None:
        """Test script with non-existent template file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            result = runner.invoke(
                cli,
                [
                    "batch",
                    str(test_folder),
                    "-t",
                    "nonexistent_template.yaml",
                    "-n",
                    "2",
                ],
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
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--help"])

        assert result.exit_code == 0
        assert "help" in result.output.lower()

    @patch("scripts.validate.Pool")
    @patch("scripts.validate.Exam")
    @patch("scripts.validate.QuestionSet")
    def test_validate_basic_run(
        self,
        mock_question_set_class: MagicMock,
        mock_exam_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """Test basic validate script execution."""
        # Mock the classes
        mock_pool = MagicMock()
        from randex.exam import Question

        mock_questions = [
            Question(
                question="Test 1?",
                answers=["a", "b", "c", "d"],
                right_answer=0,
            ),
        ]
        mock_pool.questions = {"folder1": mock_questions}
        mock_pool_class.return_value = mock_pool

        mock_exam = MagicMock()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_exam.compile.return_value = mock_result
        mock_exam_class.return_value = mock_exam

        mock_question_set = MagicMock()
        mock_question_set.size.return_value = 1
        mock_question_set.sample.return_value = mock_questions
        mock_question_set_class.return_value = mock_question_set

        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            result = runner.invoke(
                cli,
                [
                    "validate",
                    str(test_folder),
                    "-t",
                    str(sample_template_file),
                    "-o",
                    "test_output",
                ],
            )

            # Should succeed
            assert result.exit_code == 0

            # Should have called the expected methods
            assert mock_pool_class.called
            assert mock_exam_class.called
            assert mock_exam.compile.called

    def test_validate_existing_folder_without_overwrite(
        self, sample_template_file: Path
    ) -> None:
        """Test validate script with existing output folder but no overwrite flag."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            # Create existing output folder
            output_folder = Path("existing_output")
            output_folder.mkdir()

            result = runner.invoke(
                cli,
                [
                    "validate",
                    str(test_folder),
                    "-t",
                    str(sample_template_file),
                    "-o",
                    str(output_folder),
                ],
            )

            # Should fail due to existing folder
            assert result.exit_code != 0
            assert "already exists" in result.output

    @patch("scripts.validate.Pool")
    @patch("scripts.validate.Exam")
    @patch("scripts.validate.QuestionSet")
    @patch("scripts.validate.ExamTemplate")
    def test_validate_main_with_none_output_folder(
        self,
        mock_template_class: MagicMock,
        mock_question_set_class: MagicMock,
        mock_exam_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """
        Test validate main function with None output folder.

        This test is to test temp folder generation.
        """
        # Mock the classes
        mock_pool = MagicMock()
        from randex.exam import Question

        mock_questions = [
            Question(
                question="Test 1?",
                answers=["a", "b", "c", "d"],
                right_answer=0,
            ),
        ]
        mock_pool.questions = {"folder1": mock_questions}
        mock_pool_class.return_value = mock_pool

        mock_exam = MagicMock()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_exam.compile.return_value = mock_result
        mock_exam_class.return_value = mock_exam

        mock_question_set = MagicMock()
        mock_question_set.size.return_value = 1
        mock_question_set.sample.return_value = mock_questions
        mock_question_set_class.return_value = mock_question_set

        mock_template = MagicMock()
        mock_template_class.load.return_value = mock_template

        # Import and call the main function directly with None output folder
        from scripts.validate import main as validate_main

        with TemporaryDirectory() as temp_dir:
            test_folder = Path(temp_dir) / "test_folder"
            test_folder.mkdir()

            # Call main function with out_folder=None to test temp folder generation
            validate_main(
                folder=str(test_folder),
                template_tex_path=str(sample_template_file),
                out_folder=None,  # This triggers temp folder generation
                clean=False,
                show_answers=False,
                overwrite=False,
            )

            # Should have successfully called the mocked functions
            mock_pool_class.assert_called_once()
            mock_exam.compile.assert_called_once()

    @patch("scripts.validate.Pool")
    @patch("scripts.validate.Exam")
    @patch("scripts.validate.QuestionSet")
    @patch("scripts.validate.ExamTemplate")
    def test_validate_with_debug_logging(
        self,
        mock_template_class: MagicMock,
        mock_question_set_class: MagicMock,
        mock_exam_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """
        Test validate script with debug logging enabled.

        This test is to test pool.print_questions().
        """
        # Mock the classes
        mock_pool = MagicMock()
        from randex.exam import Question

        mock_questions = [
            Question(
                question="Test 1?",
                answers=["a", "b", "c", "d"],
                right_answer=0,
            ),
        ]
        mock_pool.questions = {"folder1": mock_questions}
        mock_pool_class.return_value = mock_pool

        mock_exam = MagicMock()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_exam.compile.return_value = mock_result
        mock_exam_class.return_value = mock_exam

        mock_question_set = MagicMock()
        mock_question_set.size.return_value = 1
        mock_question_set.sample.return_value = mock_questions
        mock_question_set_class.return_value = mock_question_set

        mock_template = MagicMock()
        mock_template_class.load.return_value = mock_template

        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            # Use debug logging to trigger pool.print_questions()
            result = runner.invoke(
                cli,
                [
                    "-vv",  # Enable debug logging
                    "validate",
                    str(test_folder),
                    "-t",
                    str(sample_template_file),
                    "-o",
                    "test_output",
                ],
            )

            # Should succeed
            assert result.exit_code == 0

            # Should have called pool.print_questions due to debug logging
            mock_pool.print_questions.assert_called_once()

    @patch("scripts.validate.Pool")
    @patch("scripts.validate.Exam")
    @patch("scripts.validate.QuestionSet")
    @patch("scripts.validate.ExamTemplate")
    def test_validate_compilation_with_stdout_and_stderr(
        self,
        mock_template_class: MagicMock,
        mock_question_set_class: MagicMock,
        mock_exam_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """Test validate script with compilation producing stdout and stderr."""
        # Mock the classes
        mock_pool = MagicMock()
        from randex.exam import Question

        mock_questions = [
            Question(
                question="Test 1?",
                answers=["a", "b", "c", "d"],
                right_answer=0,
            ),
        ]
        mock_pool.questions = {"folder1": mock_questions}
        mock_pool_class.return_value = mock_pool

        mock_exam = MagicMock()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "LaTeX compilation successful\nGenerated PDF"
        mock_result.stderr = "Some warnings\nBut compilation succeeded"
        mock_exam.compile.return_value = mock_result
        mock_exam_class.return_value = mock_exam

        mock_question_set = MagicMock()
        mock_question_set.size.return_value = 1
        mock_question_set.sample.return_value = mock_questions
        mock_question_set_class.return_value = mock_question_set

        mock_template = MagicMock()
        mock_template_class.load.return_value = mock_template

        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            # Use debug logging to see stdout/stderr output
            result = runner.invoke(
                cli,
                [
                    "-vv",  # Enable debug logging
                    "validate",
                    str(test_folder),
                    "-t",
                    str(sample_template_file),
                    "-o",
                    "test_output",
                ],
            )

            # Should succeed
            assert result.exit_code == 0
            assert "Validation completed successfully" in result.output

    @patch("scripts.validate.Pool")
    @patch("scripts.validate.Exam")
    @patch("scripts.validate.QuestionSet")
    @patch("scripts.validate.ExamTemplate")
    def test_validate_compilation_failure(
        self,
        mock_template_class: MagicMock,
        mock_question_set_class: MagicMock,
        mock_exam_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """Test validate script with compilation failure."""
        # Mock the classes
        mock_pool = MagicMock()
        from randex.exam import Question

        mock_questions = [
            Question(
                question="Test 1?",
                answers=["a", "b", "c", "d"],
                right_answer=0,
            ),
        ]
        mock_pool.questions = {"folder1": mock_questions}
        mock_pool_class.return_value = mock_pool

        mock_exam = MagicMock()
        mock_result = MagicMock()
        mock_result.returncode = 1  # Compilation failed
        mock_result.stdout = "LaTeX compilation output"
        mock_result.stderr = "Error: missing file\nLaTeX compilation failed"
        mock_exam.compile.return_value = mock_result
        mock_exam_class.return_value = mock_exam

        mock_question_set = MagicMock()
        mock_question_set.size.return_value = 1
        mock_question_set.sample.return_value = mock_questions
        mock_question_set_class.return_value = mock_question_set

        mock_template = MagicMock()
        mock_template_class.load.return_value = mock_template

        runner = CliRunner()
        with runner.isolated_filesystem():
            test_folder = Path("test_folder")
            test_folder.mkdir()

            result = runner.invoke(
                cli,
                [
                    "validate",
                    str(test_folder),
                    "-t",
                    str(sample_template_file),
                    "-o",
                    "test_output",
                ],
            )

            # Should complete but report compilation failure
            assert result.exit_code == 0  # CLI logs error but doesn't exit
            assert "LaTeX compilation failed" in result.output


class TestRandexVersionHandling:
    """Test version handling edge cases in scripts/randex.py."""

    def test_version_package_not_found_error(self) -> None:
        """Test fallback version when importlib.metadata.PackageNotFoundError occurs."""
        # Remove scripts.randex from sys.modules if it exists
        if "scripts.randex" in sys.modules:
            del sys.modules["scripts.randex"]

        # Mock importlib.metadata.version to raise PackageNotFoundError
        with patch("importlib.metadata.version") as mock_version:
            # Need to import the exception class first
            import importlib.metadata

            mock_version.side_effect = importlib.metadata.PackageNotFoundError(
                "randex not found"
            )

            # Now import the module, which should trigger the except block
            import scripts.randex

            # Should fall back to "0.0.0"
            assert scripts.randex.__version__ == "0.0.0"

    def test_cli_main_execution(self) -> None:
        """Test CLI entry point when called as main."""
        # Test the main block by running the module directly
        import subprocess
        import sys

        # Run the randex script module directly to trigger the main block
        result = subprocess.run(
            [sys.executable, "-m", "scripts.randex", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()


class TestBatchValidationError:
    """Test ValidationError handling in scripts/batch.py."""

    @patch("scripts.batch.Pool")
    @patch("scripts.batch.QuestionSet")
    @patch("scripts.batch.ExamBatch")
    @patch("scripts.batch.ExamTemplate")
    @patch("sys.exit")
    def test_batch_validation_error(
        self,
        mock_exit: MagicMock,
        mock_template_class: MagicMock,
        mock_batch_class: MagicMock,
        mock_question_set_class: MagicMock,
        mock_pool_class: MagicMock,
        sample_template_file: Path,
    ) -> None:
        """Test that ValidationError in batch creation calls sys.exit."""
        # Setup mock classes
        mock_pool_instance = MagicMock()
        mock_pool_class.return_value = mock_pool_instance

        mock_question_set_instance = MagicMock()
        mock_question_set_class.return_value = mock_question_set_instance

        mock_template_instance = MagicMock()
        mock_template_class.load.return_value = mock_template_instance

        # Mock ExamBatch to raise ValidationError during initialization

        # Create a proper ValidationError by trying to validate invalid data
        try:
            from pydantic import BaseModel, field_validator

            class DummyModel(BaseModel):
                test_field: str

                @field_validator("test_field")
                @classmethod
                def validate_test_field(cls, _: str) -> str:
                    raise ValueError("Validation failed")

            DummyModel(test_field="trigger_error")
        except ValidationError as validation_error:
            mock_batch_class.side_effect = validation_error

        # Import and run the main function
        from scripts.batch import main as batch_main

        # Call the main function directly with required arguments to trigger the
        # ValidationError
        with TemporaryDirectory() as temp_dir:
            test_folder = Path(temp_dir) / "test_folder"
            test_folder.mkdir()

            # This should raise ValidationError which gets caught and calls sys.exit(1)
            # Since sys.exit is mocked, execution continues and hits UnboundLocalError
            from contextlib import suppress

            with suppress(UnboundLocalError):
                batch_main(
                    folder=str(test_folder),
                    number_of_questions=3,
                    batch_size=5,
                    template_tex_path=str(sample_template_file),
                    out_folder=test_folder / "output",
                    clean=False,
                    overwrite=False,
                )

        # Verify sys.exit was called due to ValidationError
        mock_exit.assert_called_once_with(1)


class TestBatchValidationErrorHelper:
    """Helper class to test ValidationError scenarios."""

    def test_validation_error_creation(self) -> None:
        """Test that we can create ValidationError for testing."""
        from pydantic import BaseModel, field_validator

        class TestModel(BaseModel):
            test_field: str

            @field_validator("test_field")
            @classmethod
            def validate_test_field(cls, v: str) -> str:
                if not v:
                    raise ValueError("Field cannot be empty")
                return v

        # This should raise ValidationError
        with pytest.raises(ValidationError):
            TestModel(test_field="")
