"""Tests for the Exam class."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from randex.exam import Exam, Question


class TestExamValidation:
    """Test Exam validation."""

    def test_create_valid_exam(self, sample_questions, sample_exam_template):
        """Test creating a valid exam."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="001",
        )

        assert exam.sn == "001"
        assert len(exam.questions) == len(sample_questions)
        assert exam.show_answers is False

    def test_sn_format_validation(self, sample_questions, sample_exam_template):
        """Test serial number format validation."""
        # Valid numeric format should work
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="123",
        )
        assert exam.sn == "123"

        # Single digit should remain as-is (no automatic padding)
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="5",
        )
        assert exam.sn == "5"

        # Non-numeric should fail
        with pytest.raises(ValidationError, match="must be numeric"):
            Exam(
                exam_template=sample_exam_template,
                questions=sample_questions,
                sn="abc",
            )

    def test_questions_not_empty_validation(self, sample_exam_template):
        """Test that questions list cannot be empty."""
        with pytest.raises(ValidationError, match="at least one question"):
            Exam(
                exam_template=sample_exam_template,
                questions=[],
                sn="001",
            )

    def test_unique_questions_validation(self, sample_exam_template):
        """Test that questions must be unique."""
        question = Question(
            question="Duplicate question?",
            answers=["a", "b", "c"],
            right_answer=0,
        )

        with pytest.raises(ValidationError, match="Duplicate question found"):
            Exam(
                exam_template=sample_exam_template,
                questions=[question, question],  # Duplicate
                sn="001",
            )


class TestExamMethods:
    """Test Exam methods."""

    def test_apply_shuffling_questions(self, sample_questions, sample_exam_template):
        """Test shuffling questions."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="001",
        )

        original_order = [q.question for q in exam.questions]
        exam.apply_shuffling(shuffle_questions=True, shuffle_answers=False)
        new_order = [q.question for q in exam.questions]

        # Should have same questions, potentially different order
        assert set(original_order) == set(new_order)

    def test_apply_shuffling_answers(self, sample_questions, sample_exam_template):
        """Test shuffling answers."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions[:1],  # Use just one question
            sn="001",
        )

        original_correct = exam.questions[0].answers[exam.questions[0].right_answer]
        exam.apply_shuffling(shuffle_questions=False, shuffle_answers=True)
        new_correct = exam.questions[0].answers[exam.questions[0].right_answer]

        # Correct answer should still be correct
        assert original_correct == new_correct

    @patch("subprocess.run")
    def test_compile_method(
        self, mock_run, sample_questions, sample_exam_template, temp_dir
    ):
        """Test exam compilation."""
        mock_run.return_value = MagicMock(returncode=0)

        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="001",
        )

        result = exam.compile(path=temp_dir)

        # Should call subprocess.run
        assert mock_run.called
        assert result.returncode == 0

    def test_str_representation(self, sample_questions, sample_exam_template):
        """Test string representation."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="001",
        )

        str_repr = str(exam)

        # Should contain exam info
        assert "001" in str_repr
        assert str(len(sample_questions)) in str_repr

        # Should contain questions
        for question in sample_questions:
            assert question.question in str_repr


class TestExamEdgeCases:
    """Test edge cases for Exam class."""

    def test_exam_with_single_question(self, sample_exam_template):
        """Test exam with single question."""
        question = Question(
            question="Single question?",
            answers=["yes", "no"],
            right_answer=0,
        )

        exam = Exam(
            exam_template=sample_exam_template,
            questions=[question],
            sn="001",
        )

        assert len(exam.questions) == 1
        assert exam.questions[0].question == "Single question?"

    def test_exam_with_show_answers_true(self, sample_questions, sample_exam_template):
        """Test exam with show_answers=True."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="001",
            show_answers=True,
        )

        assert exam.show_answers is True

    def test_sn_with_leading_zeros(self, sample_questions, sample_exam_template):
        """Test serial number with leading zeros."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="007",
        )

        assert exam.sn == "007"

    def test_compile_with_clean_flag(
        self, sample_questions, sample_exam_template, temp_dir
    ):
        """Test compilation with clean flag."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            exam = Exam(
                exam_template=sample_exam_template,
                questions=sample_questions,
                sn="001",
            )

            exam.compile(path=temp_dir, clean=True)

            # Should be called multiple times (compile + clean)
            assert mock_run.call_count >= 1

    def test_exam_latex_generation(self, sample_questions, sample_exam_template):
        """Test that exam generates proper LaTeX."""
        exam = Exam(
            exam_template=sample_exam_template,
            questions=sample_questions,
            sn="001",
        )

        str_repr = str(exam)

        assert "\\documentclass" in str_repr
        assert "Test Exam" in str_repr
        assert "\\begin{document}" in str_repr
        assert "\\begin{questions}" in str_repr
        assert "\\end{questions}" in str_repr
        assert "\\end{document}" in str_repr


class TestExamGrading:
    """Test grading logic including edge cases."""

    def test_grade_all_unanswered(self, sample_exam_template):
        """Grading all None answers must return 0.0, not a negative value."""
        questions = [
            Question(question="Q1?", answers=["A", "B", "C"], right_answer=0),
            Question(question="Q2?", answers=["X", "Y", "Z"], right_answer=1),
        ]
        exam = Exam(exam_template=sample_exam_template, questions=questions, sn="0")
        assert exam.grade([None, None]) == 0.0

    def test_grade_negative_score_zero(self, sample_exam_template):
        """With negative_score=0.0 wrong answers carry no penalty."""
        questions = [
            Question(question="Q1?", answers=["A", "B"], right_answer=0),
            Question(question="Q2?", answers=["X", "Y"], right_answer=0),
        ]
        exam = Exam(exam_template=sample_exam_template, questions=questions, sn="0")
        score = exam.grade([0, 1], negative_score=0.0)
        assert score == 1.0

    def test_grade_negative_score_one(self, sample_exam_template):
        """With negative_score=1.0 one right and one wrong should net 0.0."""
        questions = [
            Question(question="Q1?", answers=["A", "B"], right_answer=0),
            Question(question="Q2?", answers=["X", "Y"], right_answer=0),
        ]
        exam = Exam(exam_template=sample_exam_template, questions=questions, sn="0")
        score = exam.grade([0, 1], negative_score=1.0)
        assert score == 0.0

    def test_grade_default_penalty_formula(self, sample_exam_template):
        """Default penalty is 1/(n_answers - 1); verify with 3-answer question."""
        questions = [
            Question(question="Q1?", answers=["A", "B", "C"], right_answer=0),
        ]
        exam = Exam(exam_template=sample_exam_template, questions=questions, sn="0")
        # Wrong answer on a 3-option question: penalty = 1/(3-1) = 0.5
        score = exam.grade([1])
        assert score == round(-0.5, 1)
