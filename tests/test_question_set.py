"""Tests for the QuestionSet class."""

from collections import OrderedDict

import pytest

from randex.exam import Question, QuestionSet


class TestQuestionSet:
    """Test QuestionSet class."""

    def test_create_question_set(self, sample_questions):
        """Test creating a QuestionSet."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],
                "folder2": sample_questions[2:],
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        assert len(question_set.questions) == 2
        assert "folder1" in question_set.questions
        assert "folder2" in question_set.questions

    def test_fix_keys_validator(self, sample_questions):
        """Test that keys are converted from Path to string."""
        from pathlib import Path

        # Create with Path keys
        questions_dict = {
            Path("folder1"): sample_questions[:2],
            Path("folder2"): sample_questions[2:],
        }

        question_set = QuestionSet(questions=questions_dict)

        # Keys should be strings
        for key in question_set.questions:
            assert isinstance(key, str)

        assert "folder1" in question_set.questions
        assert "folder2" in question_set.questions

    def test_size_property(self, sample_questions):
        """Test the size property."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],  # 2 questions
                "folder2": sample_questions[2:],  # 1 question
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        assert question_set.size() == 3  # Total questions

    def test_keys_property(self, sample_questions):
        """Test the keys property."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],
                "folder2": sample_questions[2:],
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        keys = question_set.keys()

        assert isinstance(keys, list)
        assert "folder1" in keys
        assert "folder2" in keys
        assert len(keys) == 2


class TestQuestionSetSampling:
    """Test QuestionSet sampling functionality."""

    def test_sample_single_number(self, sample_questions):
        """Test sampling with a single number."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],
                "folder2": sample_questions[2:],
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        sampled = question_set.sample(n=2)

        assert len(sampled) == 2
        assert all(isinstance(q, Question) for q in sampled)

    def test_sample_per_folder_list(self, sample_questions):
        """Test sampling with per-folder counts."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],  # 2 questions available
                "folder2": sample_questions[2:],  # 1 question available
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        sampled = question_set.sample(n=[1, 1])  # 1 from each folder

        assert len(sampled) == 2
        assert all(isinstance(q, Question) for q in sampled)

    def test_sample_per_folder_tuple(self, sample_questions):
        """Test sampling with per-folder counts as tuple."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],
                "folder2": sample_questions[2:],
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        sampled = question_set.sample(n=(1, 1))

        assert len(sampled) == 2

    def test_sample_more_than_available_single(self, sample_questions):
        """Test sampling more questions than available (single number)."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:1],  # Only 1 question
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        with pytest.raises(
            ValueError, match="Requested .* questions, but only .* are available"
        ):
            question_set.sample(n=5)  # Try to sample 5 when only 1 available

    def test_sample_more_than_available_per_folder(self, sample_questions):
        """Test sampling more questions than available per folder."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:1],  # Only 1 question
                "folder2": sample_questions[1:2],  # Only 1 question
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        with pytest.raises(
            ValueError, match="requested .* questions, but only .* are available"
        ):
            question_set.sample(n=[2, 1])  # Try to sample 2 from folder1 with only 1

    def test_sample_zero_questions(self, sample_questions):
        """Test sampling zero questions."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions,
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        sampled = question_set.sample(n=0)

        assert len(sampled) == 0
        assert isinstance(sampled, list)

    def test_sample_with_wrong_number_of_per_folder_counts(self, sample_questions):
        """Test sampling with wrong number of per-folder counts."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions[:2],
                "folder2": sample_questions[2:],
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        # Should raise error when per-folder counts don't match folder count
        with pytest.raises(ValueError, match=r"(?s)Expected 2 integers.*but got 3\.?"):
            question_set.sample(n=[1, 1, 1])  # 3 counts for 2 folders

    def test_sample_negative_numbers(self, sample_questions):
        """Test sampling with negative numbers."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions,
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        with pytest.raises(
            ValueError,
            match="Sample larger than population or is negative",
        ):
            question_set.sample(n=-1)

        with pytest.raises(ValueError, match=r"(?s)Expected \d+ integers.*but got \d+"):
            question_set.sample(n=[1, -1])

    def test_sample_preserves_question_integrity(self, sample_questions):
        """Test that sampled questions are complete and valid."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions,
            }
        )

        question_set = QuestionSet(questions=questions_dict)
        sampled = question_set.sample(n=2)

        for question in sampled:
            assert hasattr(question, "question")
            assert hasattr(question, "answers")
            assert hasattr(question, "right_answer")
            assert 0 <= question.right_answer < len(question.answers)

    def test_sample_randomness(self, sample_questions):
        """Test that sampling produces different results (probabilistically)."""
        # Create more questions for better randomness testing
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions * 5,  # 15 questions total
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        # Sample multiple times
        samples = []
        for _ in range(10):
            sampled = question_set.sample(n=3)
            # Convert to something hashable for comparison
            sample_repr = tuple(q.question for q in sampled)
            samples.append(sample_repr)

        # Should have some variation (not all identical)
        # This is probabilistic, but with 15 questions choosing 3, very likely
        unique_samples = set(samples)
        assert len(unique_samples) > 1, "Sampling should produce some variation"


class TestQuestionSetEdgeCases:
    """Test edge cases for QuestionSet."""

    def test_empty_question_set(self):
        """Test QuestionSet with no questions."""
        question_set = QuestionSet(questions=OrderedDict())

        assert question_set.size() == 0
        assert question_set.keys() == []

        # Sampling from empty set should work for n=0
        sampled = question_set.sample(n=0)
        assert sampled == []

        # Sampling n>0 from empty set should raise error
        with pytest.raises(
            ValueError,
            match="Requested .* questions, but only .* are available",
        ):
            question_set.sample(n=1)

    def test_question_set_with_empty_folders(self, sample_questions):
        """Test QuestionSet with some empty folders."""
        questions_dict = OrderedDict(
            {
                "folder1": sample_questions,
                "folder2": [],  # Empty folder
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        assert question_set.size() == len(sample_questions)
        assert len(question_set.keys()) == 2

        # Should handle empty folders in per-folder sampling
        with pytest.raises(
            ValueError, match="requested .* questions, but only .* are available"
        ):
            question_set.sample(n=[1, 1])  # Can't sample from empty folder2

    def test_question_set_single_folder(self, sample_questions):
        """Test QuestionSet with single folder."""
        questions_dict = OrderedDict(
            {
                "only_folder": sample_questions,
            }
        )

        question_set = QuestionSet(questions=questions_dict)

        # Single number sampling should work
        sampled = question_set.sample(n=2)
        assert len(sampled) == 2

        # Per-folder sampling with single folder should work
        sampled = question_set.sample(n=[2])
        assert len(sampled) == 2
