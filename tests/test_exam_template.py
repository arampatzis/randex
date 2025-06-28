"""Tests for the ExamTemplate class."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from randex.exam import ExamTemplate


class TestExamTemplate:
    """Test ExamTemplate class."""

    def test_create_default_template(self):
        """Test creating template with default values."""
        template = ExamTemplate()

        # Should have default values
        assert "\\documentclass" in template.documentclass
        assert "\\usepackage" in template.prebegin
        assert template.lhead == ""
        assert template.chead == ""

    def test_create_custom_template(self):
        """Test creating template with custom values."""
        template = ExamTemplate(
            documentclass="\\documentclass[12pt]{exam}",
            lhead="Custom Header",
            chead="Page \\thepage",
        )

        assert template.documentclass == "\\documentclass[12pt]{exam}"
        assert template.lhead == "Custom Header"
        assert template.chead == "Page \\thepage"

    def test_load_from_dict(self):
        """Test loading template from dictionary."""
        template_data = {
            "documentclass": "\\documentclass[12pt]{exam}",
            "lhead": "Test Exam",
            "chead": "Page \\thepage",
            "prebegin": "\\usepackage{amsmath}",
        }

        template = ExamTemplate.load(template_data)

        assert template.documentclass == "\\documentclass[12pt]{exam}"
        assert template.lhead == "Test Exam"
        assert template.chead == "Page \\thepage"
        assert template.prebegin == "\\usepackage{amsmath}"

    def test_load_from_file(self, sample_template_file):
        """Test loading template from YAML file."""
        template = ExamTemplate.load(sample_template_file)

        assert "\\documentclass" in template.documentclass
        assert template.lhead == "Test Exam"
        assert template.chead == "Page \\thepage"
        assert "\\usepackage{amsmath}" in template.prebegin

    def test_load_from_none(self):
        """Test loading template from None (should return default)."""
        template = ExamTemplate.load(None)

        # Should be default template
        default_template = ExamTemplate()
        assert template.documentclass == default_template.documentclass
        assert template.prebegin == default_template.prebegin

    def test_load_from_path_object(self, sample_template_file):
        """Test loading template from Path object."""
        # sample_template_file is already a Path object
        template = ExamTemplate.load(sample_template_file)

        assert template.lhead == "Test Exam"
        assert template.chead == "Page \\thepage"

    def test_load_with_partial_template(self, temp_dir):
        """Test loading template with only some fields specified."""
        partial_data = {
            "lhead": "Partial Template",
            "chead": "Page \\thepage",
        }

        template_file = temp_dir / "partial.yaml"
        with open(template_file, "w") as f:
            yaml.dump(partial_data, f)

        template = ExamTemplate.load(template_file)

        # Specified fields should be set
        assert template.lhead == "Partial Template"
        assert template.chead == "Page \\thepage"

        # Other fields should have defaults
        assert "\\documentclass" in template.documentclass
        assert "\\usepackage" in template.prebegin

    def test_template_attributes_are_strings(self):
        """Test that all template attributes are strings."""
        template = ExamTemplate()

        assert isinstance(template.documentclass, str)
        assert isinstance(template.prebegin, str)
        assert isinstance(template.postbegin, str)
        assert isinstance(template.preend, str)
        assert isinstance(template.head, str)
        assert isinstance(template.lhead, str)
        assert isinstance(template.chead, str)

    def test_template_with_multiline_strings(self, temp_dir):
        """Test template with multiline string values."""
        template_data = {
            "prebegin": """\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{geometry}""",
            "postbegin": """\\vspace{10mm}
\\makebox[0.9\\textwidth]{Name\\enspace\\hrulefill}
\\vspace{10mm}""",
        }

        template_file = temp_dir / "multiline.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_data, f)

        template = ExamTemplate.load(template_file)

        assert "\\usepackage{amsmath}" in template.prebegin
        assert "\\usepackage{amssymb}" in template.prebegin
        assert "\\makebox" in template.postbegin
        assert "\\vspace" in template.postbegin


class TestExamTemplateEdgeCases:
    """Test edge cases for ExamTemplate."""

    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file returns default template."""
        # The implementation logs a warning and returns default template
        template = ExamTemplate.load(Path("/nonexistent/file.yaml"))

        # Should return default template
        default_template = ExamTemplate()
        assert template.documentclass == default_template.documentclass
        assert template.prebegin == default_template.prebegin

    def test_load_from_invalid_yaml(self, temp_dir):
        """Test loading from invalid YAML file."""
        invalid_file = temp_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            ExamTemplate.load(invalid_file)

    def test_load_from_empty_file(self, temp_dir):
        """Test loading from empty YAML file."""
        empty_file = temp_dir / "empty.yaml"
        empty_file.touch()

        template = ExamTemplate.load(empty_file)

        # Should use defaults
        default_template = ExamTemplate()
        assert template.documentclass == default_template.documentclass

    def test_load_from_file_with_unknown_fields(self, temp_dir):
        """Test loading from file with unknown fields."""
        template_data = {
            "documentclass": "\\documentclass{exam}",
            "unknown_field": "this should be ignored",
            "another_unknown": 123,
        }

        template_file = temp_dir / "unknown_fields.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_data, f)

        # Should load successfully, ignoring unknown fields
        template = ExamTemplate.load(template_file)
        assert template.documentclass == "\\documentclass{exam}"

        # Unknown fields should not be set
        assert not hasattr(template, "unknown_field")
        assert not hasattr(template, "another_unknown")

    def test_template_with_empty_strings(self):
        """Test template with empty string values."""
        template = ExamTemplate(
            documentclass="",
            prebegin="",
            lhead="",
            chead="",
        )

        assert template.documentclass == ""
        assert template.prebegin == ""
        assert template.lhead == ""
        assert template.chead == ""

    def test_template_with_latex_special_characters(self):
        """Test template with LaTeX special characters."""
        template = ExamTemplate(
            lhead="Test & Exam \\% 100",
            chead="Page \\thepage\\\\ of \\numpages",
        )

        assert template.lhead == "Test & Exam \\% 100"
        assert template.chead == "Page \\thepage\\\\ of \\numpages"

    def test_load_with_different_types(self, temp_dir):
        """Test loading with different data types in YAML fails validation."""
        template_data = {
            "documentclass": "\\documentclass{exam}",
            "lhead": 123,  # Number - should cause validation error
            "chead": True,  # Boolean - should cause validation error
        }

        template_file = temp_dir / "mixed_types.yaml"
        with open(template_file, "w") as f:
            yaml.dump(template_data, f)

        # Should raise validation error for non-string types
        with pytest.raises(ValidationError):
            ExamTemplate.load(template_file)
