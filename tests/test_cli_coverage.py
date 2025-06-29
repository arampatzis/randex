"""Tests to improve coverage for CLI modules."""

import csv
from unittest.mock import Mock, patch
from urllib.error import URLError

import pytest
import yaml

from randex.exam import ExamBatch, ExamTemplate, Pool, QuestionSet


class TestDownloadExamples:
    """Test cli/download_examples.py for coverage."""

    @patch("cli.download_examples.DEST_DIR")
    def test_download_examples_destination_exists(self, mock_dest):
        """Test when destination folder already exists."""
        from cli.download_examples import main

        mock_dest.exists.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("cli.download_examples.DEST_DIR")
    def test_download_examples_url_error(self, mock_dest):
        """Test URLError during download."""
        from cli.download_examples import main

        mock_dest.exists.return_value = False

        with patch("urllib.request.urlopen", side_effect=URLError("Network error")):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("cli.download_examples.DEST_DIR")
    def test_download_examples_bad_zip(self, mock_dest):
        """Test BadZipFile error."""
        from cli.download_examples import main

        mock_dest.exists.return_value = False
        mock_response = Mock()
        mock_response.read.return_value = b"not a zip file"

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("cli.download_examples.DEST_DIR")
    def test_download_examples_os_error(self, mock_dest):
        """Test OSError during file operations."""
        from cli.download_examples import main

        mock_dest.exists.return_value = False

        with patch("tempfile.mkdtemp", side_effect=OSError("Permission denied")):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_download_examples_import_and_main_function(self):
        """Test that the module can be imported and main function exists."""
        # Simple test to ensure the module loads and main function exists
        try:
            import cli.download_examples

            assert hasattr(cli.download_examples, "main")
            assert callable(cli.download_examples.main)
        except ImportError:
            pytest.fail("Could not import cli.download_examples")


class TestCLIRandomAnswers:
    """Test cli/random_answers.py edge cases."""

    def test_random_answers_edge_cases(self, temp_dir):
        """Test edge cases in random_answers script."""
        from cli.random_answers import main

        # Create sample batch
        folder = temp_dir / "questions"
        folder.mkdir()

        question_file = folder / "q1.yaml"
        question_data = {
            "question": "Test question?",
            "answers": ["A", "B", "C", "D"],
            "right_answer": 1,
        }
        with open(question_file, "w") as f:
            yaml.dump(question_data, f)

        # Create a batch with more than 2 exams to test different cases
        pool = Pool(folder=folder)
        question_set = QuestionSet(questions=pool.questions)
        template = ExamTemplate()

        batch = ExamBatch(
            N=5,  # Test cases: 0, 1, 2, and others
            questions_set=question_set,
            exam_template=template,
            n=1,
        )
        batch.make_batch()

        # Save batch
        batch_file = temp_dir / "batch.yaml"
        batch.save(batch_file)

        # Test the random_answers script
        main(batch_file)

        # Check that the CSV file was created with all expected cases
        csv_file = temp_dir / "random_answers.csv"
        assert csv_file.exists()

        # Read and verify CSV contents
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5  # Should have 5 exams


class TestCLIValidate:
    """Test cli/validate.py edge cases."""

    def test_validate_edge_cases(self, temp_dir):
        """Test edge cases in validate script."""
        from cli.validate import main

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

        # Create template
        template_file = temp_dir / "template.yaml"
        template_data = {
            "documentclass": "\\documentclass{exam}",
            "prebegin": "\\usepackage{amsmath}",
            "postbegin": "\\begin{document}",
            "preend": "\\end{document}",
            "head": "",
            "lhead": "Test",
            "chead": "",
            "rhead": "",
        }
        with open(template_file, "w") as f:
            yaml.dump(template_data, f)

        # Test validate with different options
        output_folder = temp_dir / "validate_output"

        # Test without overwrite (should pass)
        main(
            folder=str(folder),
            template_tex_path=template_file,
            out_folder=output_folder,
            clean=False,
            show_answers=True,
            overwrite=False,
        )

        # Verify output folder was created
        assert output_folder.exists()


class TestCLIGrade:
    """Test cli/grade.py edge cases."""

    def test_grade_edge_cases(self, temp_dir):
        """Test edge cases in grade script."""
        from cli.grade import main

        # Create sample batch and answers
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
            N=3,
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
            f.write("2,\n")  # Empty answer (None)

        # Test grade script with different parameters
        main(batch_file, answers_file)

        # Test with custom negative score
        main(batch_file, answers_file, negative_score=0.25)
