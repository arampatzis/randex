"""Tests for the ExamBatch class."""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
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

    def test_validate_N_positive(self, sample_questions, sample_exam_template):  # noqa: N802
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
        for exam in batch.exams.values():
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
        for exam in batch.exams.values():
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
        batch.compile(path=temp_dir, parallel=False)

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
        for exam in batch.exams.values():
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
        serial_numbers = [exam.sn for exam in batch.exams.values()]
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
        serial_numbers = [exam.sn for exam in batch.exams.values()]
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
            batch.compile(path=temp_dir, clean=True, parallel=False)

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

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_parallel_compilation(
        self, mock_exists, mock_run, sample_questions, sample_exam_template, temp_dir
    ):
        """Test parallel compilation functionality."""
        # Test that the parallel path is exercised, but fall back to sequential for
        # actual testing
        mock_run.return_value = MagicMock(returncode=0)
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

        # Test that the parallel=True parameter works by falling back to sequential
        # when needed. This tests the code path without multiprocessing complications
        with patch.object(batch, "_run_parallel_compilation") as mock_parallel:
            # Mock parallel compilation to return results like sequential.
            # No PDFs, no failures
            mock_parallel.return_value = ([], [])

            # This should not raise an error about no PDFs since we're mocking the
            # parallel method.
            with (
                patch("randex.exam.PdfWriter"),
                pytest.raises(RuntimeError, match="No exams compiled successfully"),
            ):
                batch.compile(path=temp_dir, parallel=True)

            # Verify parallel compilation method was called
            mock_parallel.assert_called_once()

    def test_compile_single_exam_static_method(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test the _compile_single_exam static method."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True

            questions_dict = OrderedDict({"folder1": sample_questions})
            question_set = QuestionSet(questions=questions_dict)

            batch = ExamBatch(
                N=1,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=2,
            )
            batch.make_batch()

            # Test the static method directly
            exam = batch.exams[0]
            exam_data = exam.model_dump(mode="json")
            exam_dir = temp_dir / "test_exam"

            result = ExamBatch._compile_single_exam(exam_data, exam_dir, False)

            # Should return success
            serial_number, success, error_msg = result
            assert success is True
            assert serial_number == exam.sn
            assert error_msg == ""

    def test_compile_single_exam_failure(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test _compile_single_exam with compilation failure."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_run.return_value = MagicMock(returncode=1)  # Failure
            mock_exists.return_value = False  # No PDF created

            questions_dict = OrderedDict({"folder1": sample_questions})
            question_set = QuestionSet(questions=questions_dict)

            batch = ExamBatch(
                N=1,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=2,
            )
            batch.make_batch()

            # Test the static method with failure
            exam = batch.exams[0]
            exam_data = exam.model_dump(mode="json")
            exam_dir = temp_dir / "test_exam"

            result = ExamBatch._compile_single_exam(exam_data, exam_dir, False)

            # Should return failure
            serial_number, success, error_msg = result
            assert success is False
            assert serial_number == exam.sn
            assert "LaTeX compilation failed" in error_msg

    def test_compile_single_exam_exception(self, temp_dir):
        """Test _compile_single_exam with invalid data."""
        # Test with invalid exam data
        invalid_exam_data = {"invalid": "data"}
        exam_dir = temp_dir / "test_exam"

        result = ExamBatch._compile_single_exam(invalid_exam_data, exam_dir, False)

        # Should return error
        serial_number, success, error_msg = result
        assert success is False
        assert serial_number == "unknown"
        assert error_msg  # Should have some error message

    def test_pdf_sorting_functionality(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test that PDFs are sorted by serial number."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
            patch("randex.exam.PdfWriter") as mock_pdf_writer,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            mock_exists.return_value = True
            mock_writer_instance = MagicMock()
            mock_pdf_writer.return_value = mock_writer_instance

            questions_dict = OrderedDict({"folder1": sample_questions})
            question_set = QuestionSet(questions=questions_dict)

            batch = ExamBatch(
                N=3,
                questions_set=question_set,
                exam_template=sample_exam_template,
                n=2,
            )

            batch.make_batch()

            # Create fake PDF directories in random order
            (temp_dir / "2").mkdir()
            (temp_dir / "0").mkdir()
            (temp_dir / "1").mkdir()

            # Create fake PDF files
            (temp_dir / "2" / "exam.pdf").touch()
            (temp_dir / "0" / "exam.pdf").touch()
            (temp_dir / "1" / "exam.pdf").touch()

            batch.compile(path=temp_dir, parallel=False)

            # Verify PDFs were added in sorted order (0, 1, 2)
            append_calls = mock_writer_instance.append.call_args_list
            assert len(append_calls) == 3

            # Check that PDFs were appended in sorted order by serial number
            pdf_paths = [call[0][0] for call in append_calls]
            # Extract serial numbers from paths to verify order
            serial_numbers = [path.parent.name for path in pdf_paths]
            assert serial_numbers == ["0", "1", "2"]

    def test_run_parallel_compilation_method(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """
        Test the _run_parallel_compilation method directly with ThreadPoolExecutor.

        This approach avoids pickling issues.
        """
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        batch.make_batch()

        # Create directories and actual PDF files
        for exam in batch.exams.values():
            exam_dir = temp_dir / exam.sn
            exam_dir.mkdir(parents=True, exist_ok=True)
            pdf_file = exam_dir / "exam.pdf"
            pdf_file.write_bytes(b"fake pdf content")

        # Use ThreadPoolExecutor instead of ProcessPoolExecutor to avoid pickling issues
        with (
            patch("randex.exam.ProcessPoolExecutor", ThreadPoolExecutor),
            patch("randex.exam.ExamBatch._compile_single_exam") as mock_compile,
        ):

            def mock_compile_func(exam_data, exam_dir, clean):
                # Arguments used in function body
                _ = exam_dir, clean
                return exam_data["sn"], True, ""

            mock_compile.side_effect = mock_compile_func

            # Test the parallel compilation method directly
            pdf_files, failed = batch._run_parallel_compilation(temp_dir, False)

        assert len(pdf_files) == 2
        assert len(failed) == 0
        assert all(isinstance(pdf_path, Path) for pdf_path in pdf_files)

    def test_run_sequential_compilation_method(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test the _run_sequential_compilation method directly."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_run.return_value = MagicMock(returncode=0)
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

            # Test the sequential compilation method directly
            pdf_files, failed = batch._run_sequential_compilation(temp_dir, False)

            assert len(pdf_files) == 2
            assert len(failed) == 0
            assert all(isinstance(pdf_path, Path) for pdf_path in pdf_files)

    def test_compile_raises_without_make_batch(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """compile() must raise a clear RuntimeError if make_batch() was not called."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )

        with pytest.raises(RuntimeError, match="make_batch"):
            batch.compile(path=temp_dir, parallel=False)

    def test_save_load_roundtrip_fidelity(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """save() then load() must produce identical question data."""
        questions_dict = OrderedDict({"folder1": sample_questions})
        question_set = QuestionSet(questions=questions_dict)

        original = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=sample_exam_template,
            n=2,
        )
        original.make_batch()

        # Capture signatures before saving
        def signatures(batch: ExamBatch) -> list[tuple]:
            result = []
            for exam in batch.exams.values():
                result.extend(
                    (q.question, tuple(q.answers), q.right_answer)
                    for q in exam.questions
                )
            return result

        original_sigs = signatures(original)
        original_sns = [exam.sn for exam in original.exams.values()]

        save_path = temp_dir / "batch.yaml"
        original.save(save_path)
        loaded = ExamBatch.load(save_path)

        assert signatures(loaded) == original_sigs
        assert [exam.sn for exam in loaded.exams.values()] == original_sns
