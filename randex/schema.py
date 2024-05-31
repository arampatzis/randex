"""General utilities for the parser."""
from pathlib import Path

import pprintpp as pp
import yaml
from cerberus import TypeDefinition, Validator


class RandexValidator(Validator):
    """Custom validator for the TSF package."""

    def _check_with_positive(self, field, value):
        """Test whether a certain field has a positive value."""
        if value <= 0:
            self._error(field, "Must be a positive number.")

    def _check_with_nonnegative_elements(self, field, value):
        """Test that all elements in the list are positive."""
        if isinstance(value, list) and not all(item >= 0 for item in value):
            self._error(field, "All elements must be non-negative numbers")

    def _validate_match_length(self, other, field, value):
        """
        Test if two lists have the same length.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        if other not in self.document:
            return False

        if len(value) != len(self.document[other]):
            self._error(field, f"Length does not match the length of '{other}'.")
            return None
        return None

    def _validate_leq_length(self, other, field, value):
        """
        Test if a list has length less or equal than some other list.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        if other not in self.document:
            return False

        if len(value) > len(self.document[other]):
            self._error(
                field,
                f"length of {field} is greater than the length of '{other}'.",
            )
            return None
        return None

    def _validate_elements_leq_length(self, other, field, value):
        """
        Test if a list has elements less than the length of some other list.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        if other not in self.document:
            return False

        len_other = len(self.document[other])

        for v in value:
            if v >= len_other:
                self._error(
                    field,
                    (
                        f"item with value {v} is greater or equal than the length "
                        f"of '{other}'({len_other})."
                    ),
                )
        return None


RandexValidator.types_mapping["path"] = TypeDefinition("path", (Path,), ())


def validate(schema: dict, document: dict | Path) -> dict:
    """
    Validate a dictionary, or load the dictionary from a yaml file,
    against schema using Cerberus.
    """
    if isinstance(document, Path):
        with open(document) as f:
            document = yaml.safe_load(f)

    v = RandexValidator(schema, require_all=True)
    if v.validate(document):
        return v.document

    e = pp.pformat(v.errors)
    raise RuntimeError(f"Error in Cerberus:\n{e}")
