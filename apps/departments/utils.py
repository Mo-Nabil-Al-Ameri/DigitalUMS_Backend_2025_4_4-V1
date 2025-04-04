"""
وحدة المساعدة لتطبيق الأقسام
تحتوي على دوال مساعدة مثل توليد الاختصارات وتنسيق الأرقام
"""

from typing import Type, Optional
from django.db import models
from django.utils.text import slugify
from django.db.models import Max, F, Value, CharField
from django.db.models.functions import Substr, Cast, RegexpReplace
from apps.core.numbering import BaseNumberingSystem, DepartmentNumbering

def generate_department_code(name: str, max_length: Optional[int] = None) -> str:
    """توليد اختصار القسم من اسمه
    
    Args:
        name (str): اسم القسم
        max_length (Optional[int]): الحد الأقصى لطول الاختصار
        
    Returns:
        str: اختصار القسم
        
    Examples:
        >>> generate_department_code("قسم علوم الحاسب")
        'قعح'
        >>> generate_department_code("Department of Computer Science")
        'DCS'
        >>> generate_department_code("قسم علوم الحاسب", max_length=2)
        'قع'
    """
    # تنظيف النص وتقسيمه إلى كلمات
    words = slugify(name).replace('-', ' ').split()
    
    if not words:
        return ''
    
    # أخذ الحرف الأول من كل كلمة
    code = ''.join(word[0].upper() for word in words if word)
    
    # تقليص طول الاختصار إذا تم تحديد الحد الأقصى
    if max_length and len(code) > max_length:
        code = code[:max_length]
    
    return code

def generate_department_number(model_class: Type[models.Model], college_id: Optional[int] = None, department_type: str = 'academic') -> int:
    """توليد رقم القسم تلقائياً
    
    Args:
        model_class: نموذج القسم
        college_id: معرف الكلية (للأقسام الأكاديمية)
        department_type: نوع القسم (academic/administrative)
        
    Returns:
        int: رقم القسم الجديد
        
    Raises:
        ValidationError: إذا تم تجاوز الحد الأقصى للأقسام
    """
    settings = DepartmentNumbering.get_settings()
    
    if department_type == 'academic' and college_id:
        # قسم أكاديمي مرتبط بكلية
        next_number = BaseNumberingSystem.get_next_sequence(
            model=model_class,
            field_name='dep_no',
            min_val=settings['min_number'],
            max_val=settings['max_number'],
            college_id=college_id,
            department_type=department_type
        )
    else:
        # قسم إداري أو قسم مستقل
        next_number = BaseNumberingSystem.get_next_sequence(
            model=model_class,
            field_name='dep_no',
            min_val=settings['min_number'],
            max_val=settings['max_number'],
            college_id__isnull=True,
            department_type=department_type
        )
    
    return next_number

def format_department_number(number: int, college_code: Optional[int] = None, department_type: str = 'academic') -> str:
    """تنسيق رقم القسم
    
    Args:
        number: رقم القسم
        college_code: رقم الكلية (للأقسام الأكاديمية)
        department_type: نوع القسم
        
    Returns:
        str: رقم القسم المنسق
        
    Examples:
        >>> format_department_number(1, 12, 'academic')
        '12-01'
        >>> format_department_number(1, department_type='administrative')
        '01'
    """
    settings = DepartmentNumbering.get_settings()
    
    if settings['use_prefix'] and college_code and department_type == 'academic':
        # استخدام رقم الكلية كبادئة للقسم الأكاديمي
        prefix_part = BaseNumberingSystem.format_number(
            number=college_code,
            width=settings['number_width']
        )
        dept_part = BaseNumberingSystem.format_number(
            number=number,
            width=settings['number_width']
        )
        return f"{prefix_part}{settings['separator']}{dept_part}"
    else:
        # ترقيم مستقل للأقسام الإدارية
        return BaseNumberingSystem.format_number(
            number=number,
            width=settings['number_width'],
            prefix=settings['number_prefix'],
            suffix=settings['number_suffix']
        )

def validate_department_number(number: int) -> None:
    """التحقق من صحة رقم القسم
    
    Args:
        number: رقم القسم للتحقق منه
        
    Raises:
        ValidationError: إذا كان الرقم خارج النطاق المسموح به
    """
    settings = DepartmentNumbering.get_settings()
    BaseNumberingSystem.validate_range(
        number=number,
        min_val=settings['min_number'],
        max_val=settings['max_number'],
        field_name='dep_no'
    )

def get_unique_department_code(model_class: Type[models.Model], name: str, max_length: int = 10) -> str:
    """توليد اختصار فريد للقسم
    
    يقوم بتوليد اختصار من اسم القسم، ثم يتحقق من عدم وجود تكرار.
    إذا كان الاختصار مكرراً، يضيف رقماً في النهاية.
    
    Args:
        model_class: نموذج القسم
        name: اسم القسم
        max_length: الحد الأقصى لطول الاختصار
        
    Returns:
        str: اختصار فريد للقسم
        
    Examples:
        >>> get_unique_department_code(Department, "قسم علوم الحاسب")
        'قعح'
        >>> # إذا كان 'قعح' موجوداً
        >>> get_unique_department_code(Department, "قسم علوم الحاسب")
        'قعح1'
    """
    # توليد الاختصار الأساسي
    base_code = generate_department_code(name, max_length=max_length)
    
    # البحث عن الاختصارات المشابهة
    similar_codes = model_class.objects.filter(
        code__regex=f"^{base_code}[0-9]*$"
    ).annotate(
        # استخراج الرقم من نهاية الاختصار
        number=Cast(
            RegexpReplace(F('code'), f"^{base_code}", ''),
            models.IntegerField(),
            null=True
        )
    ).aggregate(
        # الحصول على أعلى رقم
        max_number=Max('number')
    )
    
    # إذا لم يكن هناك اختصار مشابه، نستخدم الاختصار الأساسي
    if not similar_codes['max_number']:
        return base_code
        
    # إضافة رقم جديد للاختصار
    next_number = similar_codes['max_number'] + 1
    return f"{base_code}{next_number}"

# function for department image path
def department_image_path(instance, filename):
    # تحويل اسم القسم والكلية إلى صيغة مناسبة للمسار
    department_slug = slugify(instance.name)
    college_slug = slugify(instance.college.name)
    # الحصول على تاريخ اليوم بصيغة معينة
    date_str = datetime.datetime.now().strftime("%Y_%m_%d")
    # دمج مسار الملف مع مسار المجلد
    full_path = os.path.join('colleges', college_slug, department_slug,'images', date_str, filename)
    return full_path

def program_plan_path(instance, filename):
    department_slug = slugify(instance.department.name)
    college_slug = slugify(instance.department.college.name)
    # الحصول على تاريخ اليوم بصيغة معينة
    program_name = slugify(instance.name)
    # دمج مسار الملف مع مسار المجلد
    full_path = os.path.join('colleges', college_slug, department_slug, 'programs_plan',program_name, filename)
    return full_path
