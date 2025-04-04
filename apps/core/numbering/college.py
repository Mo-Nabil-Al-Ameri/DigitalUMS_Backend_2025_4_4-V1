"""
College numbering system
"""

from .base import NumberingSettings


class CollegeNumbering(NumberingSettings):
    """نظام ترقيم الكليات"""
    
    DEFAULT_MIN = 1
    DEFAULT_MAX = 99
    DEFAULT_WIDTH = 2
    DEFAULT_PREFIX = ''
    DEFAULT_SUFFIX = ''
    DEFAULT_SEPARATOR = '-'
    DEFAULT_USE_PREFIX = True

    @classmethod
    def get_settings(cls) -> dict:
        """الحصول على إعدادات ترقيم الكليات"""
        return super().get_settings('COLLEGE')
