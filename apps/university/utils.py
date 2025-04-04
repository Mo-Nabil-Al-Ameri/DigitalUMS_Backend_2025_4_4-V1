"""
Utility functions for the university app
"""

from apps.core.numbering import (
    BaseNumberingSystem,
    CollegeNumbering,
    DepartmentNumbering,
    ProgramNumbering
)

__all__ = [
    'BaseNumberingSystem',
    'CollegeNumbering',
    'DepartmentNumbering',
    'ProgramNumbering',
]

"""
وحدة المساعدة لتطبيق الجامعة
تحتوي على دوال مساعدة مثل توليد وتنسيق الأرقام
"""

from typing import Type, Any
from django.db import models
from apps.core.numbering import BaseNumberingSystem, CollegeNumbering

def generate_college_number(model_class: Type[models.Model]) -> int:
    """توليد رقم الكلية تلقائياً
    
    Args:
        model_class: نموذج الكلية
        
    Returns:
        int: رقم الكلية الجديد
        
    Raises:
        ValidationError: إذا تم تجاوز الحد الأقصى للكليات
    """
    settings = CollegeNumbering.get_settings()
    
    next_number = BaseNumberingSystem.get_next_sequence(
        model=model_class,
        field_name='code',
        min_val=settings['min_number'],
        max_val=settings['max_number']
    )
    
    return next_number

def format_college_number(number: int) -> str:
    """تنسيق رقم الكلية
    
    Args:
        number: رقم الكلية
        
    Returns:
        str: رقم الكلية المنسق
        
    Examples:
        >>> format_college_number(1)
        '01'
        >>> format_college_number(12)
        '12'
    """
    settings = CollegeNumbering.get_settings()
    return BaseNumberingSystem.format_number(
        number=number,
        width=settings['number_width'],
        prefix=settings['number_prefix'],
        suffix=settings['number_suffix']
    )

def validate_college_number(number: int) -> None:
    """التحقق من صحة رقم الكلية
    
    Args:
        number: رقم الكلية للتحقق منه
        
    Raises:
        ValidationError: إذا كان الرقم خارج النطاق المسموح به
    """
    settings = CollegeNumbering.get_settings()
    BaseNumberingSystem.validate_range(
        number=number,
        min_val=settings['min_number'],
        max_val=settings['max_number'],
        field_name='code'
    )