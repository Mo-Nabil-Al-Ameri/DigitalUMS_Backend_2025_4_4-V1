"""
Department numbering system
"""

from .base import NumberingSettings


class DepartmentNumbering(NumberingSettings):
    """نظام ترقيم الأقسام"""
    
    DEFAULT_MIN = 1
    DEFAULT_MAX = 99
    DEFAULT_WIDTH = 2
    DEFAULT_PREFIX = ''
    DEFAULT_SUFFIX = ''
    DEFAULT_SEPARATOR = '-'
    DEFAULT_USE_PREFIX = True

    @classmethod
    def get_settings(cls) -> dict:
        """الحصول على إعدادات ترقيم الأقسام"""
        return super().get_settings('DEPARTMENT')
