"""Tests for the Pool class."""

from unittest.mock import patch

import pytest

from randex.exam import Pool, is_glob_expression


class TestIsGlobExpression:
    """Test the is_glob_expression utility function."""

    def test_glob_patterns(self):
        """Test various glob patterns."""
        assert is_glob_expression("*.yaml")
        assert is_glob_expression("folder_*")
        assert is_glob_expression("test?")
        assert is_glob_expression("[abc]")
        assert is_glob_expression("path/*/file")

    def test_non_glob_patterns(self):
        """Test non-glob strings."""
        assert not is_glob_expression("folder")
        assert not is_glob_expression("path/to/folder")
        assert not is_glob_expression("file.yaml")
        assert not is_glob_expression("")


class TestPool:
    """Test Pool class."""

    def test_pool_with_single_folder(self, sample_question_files):
        """Test pool creation with single folder."""
        folder1 = sample_question_files / "folder1"
        pool = Pool(folder=folder1)

        # Should have questions from folder1
        assert len(pool.questions) >= 1

        # Check that folder1 (or its resolved path) is in the questions
        # macOS can have different path representations due to symlinks
        folder1_resolved = folder1.resolve()
        found_folder = None
        for key in pool.questions:
            if key.resolve() == folder1_resolved:
                found_folder = key
                break

        assert found_folder is not None, (
            f"folder1 not found in pool.questions keys: {list(pool.questions.keys())}"
        )

        # Check questions were loaded correctly
        questions_list = pool.questions[found_folder]
        assert len(questions_list) == 2  # q1.yaml and q2.yaml

        # Verify question content
        question_texts = [q.question for q in questions_list]
        assert "What is $1+1$?" in question_texts
        assert "What is $2+2$?" in question_texts

    def test_pool_with_folder_string(self, sample_question_files):
        """Test pool creation with folder as string."""
        folder1_str = str(sample_question_files / "folder1")
        pool = Pool(folder=folder1_str)

        assert len(pool.questions) >= 1

    def test_pool_folders_property(self, sample_question_files):
        """Test the folders property."""
        pool = Pool(folder=sample_question_files)
        folders = pool.folders

        # Should be a tuple
        assert isinstance(folders, tuple)

        # Should contain both folders
        folder_names = [f.name for f in folders]
        assert "folder1" in folder_names
        assert "folder2" in folder_names

    def test_number_of_folders_property(self, sample_question_files):
        """Test the number_of_folders property."""
        pool = Pool(folder=sample_question_files)
        assert pool.number_of_folders == 2

    def test_resolve_folder_input_with_path(self, sample_question_files):
        """Test folder resolution with regular path."""
        pool = Pool(folder=sample_question_files)
        resolved = pool.resolve_folder_input()

        assert isinstance(resolved, list)
        assert len(resolved) >= 2

        # Should include subdirectories
        folder_names = [f.name for f in resolved]
        assert "folder1" in folder_names
        assert "folder2" in folder_names

    @patch("pathlib.Path.glob")
    def test_resolve_folder_input_with_glob(self, mock_glob, temp_dir):
        """Test folder resolution with glob pattern."""
        # Create actual folders to work with
        folder1 = temp_dir / "folder1"
        folder2 = temp_dir / "folder2"
        folder1.mkdir()
        folder2.mkdir()

        # Mock glob to return these paths
        mock_paths = [folder1, folder2]
        mock_glob.return_value = mock_paths

        pool = Pool(folder=f"{temp_dir}/folder_*")
        resolved = pool.resolve_folder_input()

        # Check resolved paths match mock paths (handle macOS path resolution issues)
        assert len(resolved) == len(mock_paths)
        for resolved_path, mock_path in zip(resolved, mock_paths, strict=False):
            assert resolved_path.resolve() == mock_path.resolve()
        mock_glob.assert_called_once()

    def test_pool_str_representation(self, sample_question_files):
        """Test string representation of pool."""
        pool = Pool(folder=sample_question_files)
        str_repr = str(pool)

        # Should contain folder information
        assert "folder1" in str_repr or "folder2" in str_repr

        # Should show question counts
        assert "question" in str_repr.lower()

    def test_print_questions(self, sample_question_files, capsys):
        """Test the print_questions method."""
        pool = Pool(folder=sample_question_files)
        pool.print_questions()

        captured = capsys.readouterr()

        # Should print something
        assert len(captured.out) > 0

        # Should contain question information
        assert "question" in captured.out.lower()

    def test_pool_with_empty_folder(self, temp_dir):
        """Test pool with folder containing no YAML files."""
        empty_folder = temp_dir / "empty"
        empty_folder.mkdir()

        pool = Pool(folder=empty_folder)

        # Should handle empty folder gracefully
        assert isinstance(pool.questions, dict)

    def test_pool_with_invalid_yaml(self, temp_dir):
        """Test pool with invalid YAML files."""
        folder = temp_dir / "invalid"
        folder.mkdir()

        # Create invalid YAML file
        invalid_file = folder / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        # Should handle invalid YAML gracefully by skipping invalid files
        pool = Pool(folder=folder)
        # Force evaluation - should not raise, but handle gracefully
        questions = pool.questions

        # Should handle gracefully by either loading valid questions
        # or having empty results
        assert isinstance(questions, dict)

    def test_pool_with_missing_required_fields(self, temp_dir):
        """Test pool with YAML files missing required fields."""
        folder = temp_dir / "incomplete"
        folder.mkdir()

        # Create YAML with missing fields
        incomplete_file = folder / "incomplete.yaml"
        with open(incomplete_file, "w") as f:
            f.write("question: What is this?\n")  # Missing answers and right_answer

        # Should handle incomplete questions appropriately by skipping them
        pool = Pool(folder=folder)
        # Force evaluation - should not raise, but handle gracefully
        questions = pool.questions

        # If validation happens during loading, check questions
        if questions:
            # Questions should be valid or filtered out
            for question_list in questions.values():
                for q in question_list:
                    assert hasattr(q, "question")
                    assert hasattr(q, "answers")
                    assert hasattr(q, "right_answer")
        else:
            # Or should have empty questions if all were invalid
            assert len(questions) == 0


class TestPoolEdgeCases:
    """Test edge cases for Pool class."""

    def test_pool_with_nonexistent_folder(self):
        """Test pool with non-existent folder."""
        with pytest.raises(NotADirectoryError):
            # Force evaluation of cached property during creation
            _ = Pool(folder="/nonexistent/path").questions

    def test_pool_caching_behavior(self, sample_question_files):
        """Test that cached properties work correctly."""
        pool = Pool(folder=sample_question_files)

        # Access questions multiple times
        questions1 = pool.questions
        questions2 = pool.questions

        # Should be the same object (cached)
        assert questions1 is questions2

        # Same for folders
        folders1 = pool.folders
        folders2 = pool.folders
        assert folders1 is folders2
