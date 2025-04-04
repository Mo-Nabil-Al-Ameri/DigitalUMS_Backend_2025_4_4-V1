"""
Numbering system package for managing various numbering schemes in the application.
"""

from .base import BaseNumberingSystem, NumberingSettings
from .college import CollegeNumbering
from .department import DepartmentNumbering
from .program import ProgramNumbering

__all__ = [
    'BaseNumberingSystem',
    'NumberingSettings',
    'CollegeNumbering',
    'DepartmentNumbering',
    'ProgramNumbering',
]
