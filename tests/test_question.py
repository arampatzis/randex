"""Tests for the Question class."""

import pytest

from randex.exam import Question


class TestQuestionValidation:
    """Test Question validation."""

    def test_valid_question_creation(self, sample_question_data):
        """Test creating a valid question."""
        question = Question(**sample_question_data)
        assert question.question == "What is $1+1$?"
        assert question.answers == ["0", "1", "2", "3"]
        assert question.right_answer == 2

    def test_answers_must_be_list(self):
        """Test that answers must be a list."""
        with pytest.raises(TypeError):
            Question(
                question="Test?",
                answers="not a list",
                right_answer=0,
            )

    def test_answers_converted_to_strings(self):
        """Test that answers are converted to strings."""
        question = Question(
            question="Test?",
            answers=[1, 2, 3, 4],
            right_answer=0,
        )
        assert question.answers == ["1", "2", "3", "4"]

    def test_right_answer_must_be_coercible_to_int(self):
        """Test that right_answer must be coercible to int."""
        # String that can be converted to int should work
        question = Question(
            question="Test?",
            answers=["a", "b", "c"],
            right_answer="1",
        )
        assert question.right_answer == 1

        # String that cannot be converted should fail
        with pytest.raises(TypeError):
            Question(
                question="Test?",
                answers=["a", "b", "c"],
                right_answer="not a number",
            )

    def test_right_answer_must_be_valid_index(self):
        """Test that right_answer must be a valid index."""
        # Valid index should work
        Question(
            question="Test?",
            answers=["a", "b", "c"],
            right_answer=2,
        )

        # Index out of bounds should fail
        with pytest.raises(IndexError):
            Question(
                question="Test?",
                answers=["a", "b", "c"],
                right_answer=3,
            )

        # Negative index should fail
        with pytest.raises(IndexError):
            Question(
                question="Test?",
                answers=["a", "b", "c"],
                right_answer=-1,
            )


class TestQuestionMethods:
    """Test Question methods."""

    def test_shuffle_preserves_correct_answer(self, sample_question):
        """Test that shuffling preserves the correct answer."""
        original_correct = sample_question.answers[sample_question.right_answer]
        shuffled = sample_question.shuffle()

        # Should be a new object
        assert shuffled is not sample_question

        # Correct answer should still be correct
        shuffled_correct = shuffled.answers[shuffled.right_answer]
        assert shuffled_correct == original_correct

        # Should have same answers (different order potentially)
        assert set(shuffled.answers) == set(sample_question.answers)

    def test_shuffle_multiple_times(self, sample_question):
        """Test that multiple shuffles work correctly."""
        original_correct = sample_question.answers[sample_question.right_answer]

        for _ in range(10):  # Test multiple shuffles
            shuffled = sample_question.shuffle()
            shuffled_correct = shuffled.answers[shuffled.right_answer]
            assert shuffled_correct == original_correct

    def test_to_latex_output(self, sample_question):
        """Test LaTeX output format."""
        latex_output = sample_question.to_latex()

        # Should contain question text
        assert "What is $1+1$?" in latex_output

        # Should contain LaTeX commands
        assert "\\question" in latex_output
        assert "\\begin{oneparchoices}" in latex_output
        assert "\\end{oneparchoices}" in latex_output

        # Should have correct choice marked
        assert "\\correctchoice" in latex_output

        # Should have other choices marked as regular choices
        assert "\\choice" in latex_output

        # Check that all answers are present
        for answer in sample_question.answers:
            assert answer in latex_output

    def test_to_latex_with_shuffled_question(self, sample_question):
        """Test LaTeX output with shuffled question."""
        shuffled = sample_question.shuffle()
        latex_output = shuffled.to_latex()

        # Should still have correct answer marked
        lines = latex_output.split("\n")
        correct_lines = [line for line in lines if "\\correctchoice" in line]
        assert len(correct_lines) == 1

        # The correct choice should contain the right answer
        correct_line = correct_lines[0]
        original_correct = sample_question.answers[sample_question.right_answer]
        assert original_correct in correct_line

    def test_str_representation(self, sample_question):
        """Test string representation."""
        str_repr = str(sample_question)

        # Should contain question text
        assert "What is $1+1$?" in str_repr

        # Should show all answers
        for answer in sample_question.answers:
            assert answer in str_repr

        # Should mark correct answer with checkmark
        assert "✓" in str_repr

        # Count checkmarks - should be exactly one
        checkmark_count = str_repr.count("✓")
        assert checkmark_count == 1


class TestQuestionEdgeCases:
    """Test edge cases for Question class."""

    def test_single_answer(self):
        """Test question with single answer."""
        question = Question(
            question="Only one choice?",
            answers=["Yes"],
            right_answer=0,
        )
        assert question.right_answer == 0
        assert len(question.answers) == 1

    def test_many_answers(self):
        """Test question with many answers."""
        answers = [f"Answer {i}" for i in range(10)]
        question = Question(
            question="Many choices?",
            answers=answers,
            right_answer=5,
        )
        assert question.right_answer == 5
        assert len(question.answers) == 10

    def test_empty_question_text(self):
        """Test with empty question text."""
        question = Question(
            question="",
            answers=["a", "b"],
            right_answer=0,
        )
        assert question.question == ""

    def test_answers_with_special_characters(self):
        """Test answers containing LaTeX and special characters."""
        question = Question(
            question="Math question?",
            answers=["$x^2$", "$\\sqrt{2}$", "$\\pi$", "$e$"],
            right_answer=1,
        )
        latex_output = question.to_latex()
        assert "$\\sqrt{2}$" in latex_output
        assert "\\correctchoice" in latex_output
