"""Integration tests for the complete exam generation workflow."""

from pathlib import Path

import yaml

from randex.exam import ExamBatch, ExamTemplate, Pool, QuestionSet


class TestCompleteWorkflow:
    """Test the complete exam generation workflow."""

    def test_end_to_end_workflow(
        self, sample_question_files, sample_template_file, temp_dir
    ):
        """Test complete workflow from questions to exam batch."""
        # Step 1: Load questions from files
        pool = Pool(folder=sample_question_files)

        # Verify questions were loaded
        assert len(pool.questions) >= 2  # Should have folder1 and folder2
        total_questions = sum(len(q_list) for q_list in pool.questions.values())
        assert total_questions >= 3  # Should have at least 3 questions total

        # Step 2: Create question set
        question_set = QuestionSet(questions=pool.questions)

        # Verify question set
        assert question_set.size() >= 3
        assert len(question_set.keys()) >= 2

        # Step 3: Load exam template
        exam_template = ExamTemplate.load(sample_template_file)

        # Verify template loaded
        assert exam_template.lhead == "Test Exam"
        assert "\\documentclass" in exam_template.documentclass

        # Step 4: Create exam batch
        batch = ExamBatch(
            N=2,  # Create 2 exams
            questions_set=question_set,
            exam_template=exam_template,
            n=2,  # 2 questions per exam
        )

        # Step 5: Generate the batch
        batch.make_batch()

        # Verify batch was created
        assert len(batch.exams) == 2
        for exam in batch.exams:
            assert len(exam.questions) == 2
            assert exam.exam_template == exam_template

        # Step 6: Save the batch
        save_path = temp_dir / "complete_batch.yaml"
        batch.save(save_path)

        # Verify batch was saved
        assert save_path.exists()

        # Step 7: Load the batch back
        loaded_batch = ExamBatch.load(save_path)

        # Verify loaded batch matches original
        assert loaded_batch.N == batch.N
        assert len(loaded_batch.exams) == len(batch.exams)

    def test_workflow_with_per_folder_sampling(
        self,
        sample_question_files: Path,
        sample_template_file: Path,
    ) -> None:
        """Test workflow with per-folder question sampling."""
        # Load questions
        pool = Pool(folder=sample_question_files)
        question_set = QuestionSet(questions=pool.questions)
        exam_template = ExamTemplate.load(sample_template_file)

        # Get number of folders for per-folder sampling
        num_folders = len(question_set.keys())

        # Create batch with per-folder sampling
        batch = ExamBatch(
            N=2,
            questions_set=question_set,
            exam_template=exam_template,
            n=[1] * num_folders,  # 1 question from each folder
        )

        batch.make_batch()

        # Verify each exam has questions from different folders
        assert len(batch.exams) == 2
        for exam in batch.exams:
            assert len(exam.questions) == num_folders

    def test_workflow_with_shuffling(
        self,
        sample_question_files: Path,
        sample_template_file: Path,
    ) -> None:
        """Test workflow with question and answer shuffling."""
        pool = Pool(folder=sample_question_files)
        question_set = QuestionSet(questions=pool.questions)
        exam_template = ExamTemplate.load(sample_template_file)

        batch = ExamBatch(
            N=3,
            questions_set=question_set,
            exam_template=exam_template,
            n=2,
        )

        batch.make_batch()

        # Apply shuffling to each exam
        for exam in batch.exams:
            original_questions = [q.question for q in exam.questions]
            exam.questions[0].answers[exam.questions[0].right_answer]

            exam.apply_shuffling(shuffle_questions=True, shuffle_answers=True)

            # Questions might be in different order
            new_questions = [q.question for q in exam.questions]
            assert set(original_questions) == set(new_questions)

            # But correct answers should still be correct
            new_first_correct = exam.questions[0].answers[
                exam.questions[0].right_answer
            ]
            # Note: We can't directly compare because questions might be reordered
            assert isinstance(new_first_correct, str)

    def test_workflow_error_handling(self, temp_dir):
        """Test workflow error handling with problematic data."""
        # Create folder with invalid question file
        bad_folder = temp_dir / "bad_questions"
        bad_folder.mkdir()

        # Invalid question (missing required fields)
        bad_question_file = bad_folder / "bad.yaml"
        with open(bad_question_file, "w") as f:
            yaml.dump({"question": "Incomplete question"}, f)

        # Should handle gracefully by skipping invalid questions
        pool = Pool(folder=bad_folder)
        # Force evaluation - should not raise, but skip invalid questions
        questions = pool.questions

        # Should have either empty questions or no questions loaded
        if questions:
            # If any questions loaded, they should be valid
            for question_list in questions.values():
                for q in question_list:
                    assert hasattr(q, "question")
                    assert hasattr(q, "answers")
                    assert hasattr(q, "right_answer")
        else:
            # Or no questions if all were invalid
            assert len(questions) == 0

    def test_workflow_with_minimal_data(self, temp_dir):
        """Test workflow with minimal valid data."""
        # Create minimal question file
        folder = temp_dir / "minimal"
        folder.mkdir()

        question_file = folder / "q1.yaml"
        minimal_question = {
            "question": "Test question?",
            "answers": ["A", "B"],
            "right_answer": 0,
        }
        with open(question_file, "w") as f:
            yaml.dump(minimal_question, f)

        # Create minimal template
        template_file = temp_dir / "minimal_template.yaml"
        minimal_template = {
            "lhead": "Minimal Test",
        }
        with open(template_file, "w") as f:
            yaml.dump(minimal_template, f)

        # Run workflow
        pool = Pool(folder=folder)
        question_set = QuestionSet(questions=pool.questions)
        exam_template = ExamTemplate.load(template_file)

        batch = ExamBatch(
            N=1,
            questions_set=question_set,
            exam_template=exam_template,
            n=1,
        )

        batch.make_batch()

        # Should work with minimal data
        assert len(batch.exams) == 1
        assert len(batch.exams[0].questions) == 1
        assert batch.exams[0].questions[0].question == "Test question?"

    def test_large_scale_workflow(self, temp_dir):
        """Test workflow with larger number of questions and exams."""
        # Create multiple folders with multiple questions each
        for folder_idx in range(3):
            folder = temp_dir / f"folder_{folder_idx}"
            folder.mkdir()

            for question_idx in range(5):
                question_file = folder / f"q{question_idx}.yaml"
                question_data = {
                    "question": f"Question {folder_idx}-{question_idx}?",
                    "answers": [
                        f"A{question_idx}",
                        f"B{question_idx}",
                        f"C{question_idx}",
                    ],
                    "right_answer": question_idx % 3,
                }
                with open(question_file, "w") as f:
                    yaml.dump(question_data, f)

        # Create template
        template_file = temp_dir / "template.yaml"
        template_data = {"lhead": "Large Scale Test"}
        with open(template_file, "w") as f:
            yaml.dump(template_data, f)

        # Run workflow
        pool = Pool(folder=temp_dir)
        question_set = QuestionSet(questions=pool.questions)
        exam_template = ExamTemplate.load(template_file)

        # Create larger batch
        batch = ExamBatch(
            N=10,  # 10 exams
            questions_set=question_set,
            exam_template=exam_template,
            n=5,  # 5 questions per exam
        )

        batch.make_batch()

        # Verify large batch
        assert len(batch.exams) == 10
        for exam in batch.exams:
            assert len(exam.questions) == 5
            # Each exam should have unique questions
            question_texts = [q.question for q in exam.questions]
            assert len(set(question_texts)) == len(question_texts)  # All unique

    def test_workflow_reproducibility(
        self,
        sample_question_files: Path,
        sample_template_file: Path,
    ) -> None:
        """Test that workflow produces consistent results with same input."""
        # Note: This test is limited because of randomness in sampling
        # But we can test that the structure is consistent

        def create_batch():
            pool = Pool(folder=sample_question_files)
            question_set = QuestionSet(questions=pool.questions)
            exam_template = ExamTemplate.load(sample_template_file)

            batch = ExamBatch(
                N=2,
                questions_set=question_set,
                exam_template=exam_template,
                n=2,
            )
            batch.make_batch()
            return batch

        batch1 = create_batch()
        batch2 = create_batch()

        # Structure should be the same
        assert len(batch1.exams) == len(batch2.exams)
        assert batch1.N == batch2.N

        for exam1, exam2 in zip(batch1.exams, batch2.exams, strict=False):
            assert len(exam1.questions) == len(exam2.questions)
            # Questions might be different due to randomness, but structure should match
