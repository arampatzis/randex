"""General utilities for the parser."""
import datetime
from pathlib import Path

import yaml

import pprintpp as pp
from cerberus import TypeDefinition
from cerberus import Validator


class RandexValidator(Validator):
    """Custom validator for the TSF package."""
    
    def _validate_match_length(self, other, field, value):
        """
        Test if two lists have the same length.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        
        if other not in self.document:
            return False
        
        if len(value) != len(self.document[other]):
            self._error(field, f'Length does not match the length of \'{other}\'.')

    def _validate_leq_length(self, other, field, value):
        """
        Test if a list has length less or equal than some other list.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        
        if other not in self.document:
            return False
        
        if len(value) > len(self.document[other]):
            self._error(field, f'Length greater than the length of \'{other}\'.')

    def _validate_elements_leq_length(self, other, field, value):
        """
        Test if a list has elements less or equal than the length of some other list.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        
        if other not in self.document:
            return False
        
        for v in value:
            if v > len(self.document[other]):
                self._error(field, f'{v} is greater than the length of \'{other}\'.')


RandexValidator.types_mapping['path'] = TypeDefinition('path', (Path, ), ())


def validate(schema: dict, document: dict | Path):
    """
    Validates a dictionary, or loads the dictionary from a yaml file,
    against schema using Cerberus.
    """
    
    if isinstance(document, Path):
        with open(document) as f:
            document = yaml.safe_load(f)
    
    v = RandexValidator(schema, require_all=True)
    if v.validate(document):
        return v.document

    e = pp.pformat(v.errors)
    raise RuntimeError(f'Error in Cerberus:\n{e}')
