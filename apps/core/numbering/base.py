"""
نظام الترقيم الأساسي للنظام
"""
from typing import Optional, Union, Dict, Any
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from enum import Enum

class NumberingPattern(Enum):
    """أنماط الترقيم المدعومة"""
    NUMERIC = 'numeric'  # أرقام فقط: 1, 2, 3
    ALPHA = 'alpha'  # حروف فقط: A, B, C
    ALPHANUMERIC = 'alphanumeric'  # خليط: A1, A2, B1
    NAME_BASED = 'name_based'  # مبني على الاسم: CS1, ENG2
    PARENT_BASED = 'parent_based'  # مبني على الأب: 101, 102
    CUSTOM = 'custom'  # نمط مخصص

class BaseNumberingSystem:
    """نظام الترقيم العام - يدعم أنماط متعددة لتوليد وتنسيق الأرقام أو الرموز"""

    # الإعدادات الافتراضية
    DEFAULT_PATTERN = NumberingPattern.NUMERIC
    DEFAULT_PREFIX = ''
    DEFAULT_SUFFIX = ''
    DEFAULT_SEPARATOR = '-'
    DEFAULT_MIN_VALUE = 1
    DEFAULT_MAX_VALUE = 999
    DEFAULT_PADDING = 3
    DEFAULT_IGNORED_WORDS = {'and', 'of', 'the', 'في', 'من', 'ال', 'و'}

    @classmethod
    def get_settings(cls, key: str) -> dict:
        """الحصول على إعدادات الترقيم من ملف الإعدادات
        
        Args:
            key: مفتاح الإعدادات (مثل 'COLLEGE' أو 'DEPARTMENT')
            
        Returns:
            dict: الإعدادات المستخرجة من ملف الإعدادات أو الافتراضية
        """
        default_settings = {
            'pattern': cls.DEFAULT_PATTERN,
            'prefix': cls.DEFAULT_PREFIX,
            'suffix': cls.DEFAULT_SUFFIX,
            'separator': cls.DEFAULT_SEPARATOR,
            'min_value': cls.DEFAULT_MIN_VALUE,
            'max_value': cls.DEFAULT_MAX_VALUE,
            'padding': cls.DEFAULT_PADDING,
            'ignored_words': cls.DEFAULT_IGNORED_WORDS
        }
        
        return getattr(settings, f'{key}_NUMBERING_SETTINGS', default_settings)

    def __init__(
        self,
        pattern=None,
        prefix=None,
        suffix=None,
        separator=None,
        min_value=None,
        max_value=None,
        padding=None,
        ignored_words=None,
        settings_key=None
    ):
        # استخراج الإعدادات من ملف الإعدادات إذا تم تحديد المفتاح
        if settings_key:
            config = self.get_settings(settings_key)
            self.pattern = pattern or config.get('pattern', self.DEFAULT_PATTERN)
            self.prefix = prefix or config.get('prefix', self.DEFAULT_PREFIX)
            self.suffix = suffix or config.get('suffix', self.DEFAULT_SUFFIX)
            self.separator = separator or config.get('separator', self.DEFAULT_SEPARATOR)
            self.min_value = min_value or config.get('min_value', self.DEFAULT_MIN_VALUE)
            self.max_value = max_value or config.get('max_value', self.DEFAULT_MAX_VALUE)
            self.padding = padding or config.get('padding', self.DEFAULT_PADDING)
            self.ignored_words = ignored_words or config.get('ignored_words', self.DEFAULT_IGNORED_WORDS)
        else:
            # استخدام القيم المحددة أو الافتراضية
            self.pattern = pattern or self.DEFAULT_PATTERN
            self.prefix = prefix or self.DEFAULT_PREFIX
            self.suffix = suffix or self.DEFAULT_SUFFIX
            self.separator = separator or self.DEFAULT_SEPARATOR
            self.min_value = min_value or self.DEFAULT_MIN_VALUE
            self.max_value = max_value or self.DEFAULT_MAX_VALUE
            self.padding = padding or self.DEFAULT_PADDING
            self.ignored_words = ignored_words or self.DEFAULT_IGNORED_WORDS

    def generate_number(self, model_class, **kwargs):
        """توليد رقم جديد حسب النمط المحدد"""
        if self.pattern == NumberingPattern.NUMERIC:
            return self._generate_numeric(model_class)
        elif self.pattern == NumberingPattern.ALPHA:
            return self._generate_alpha(model_class)
        elif self.pattern == NumberingPattern.ALPHANUMERIC:
            return self._generate_alphanumeric(model_class, **kwargs)
        elif self.pattern == NumberingPattern.NAME_BASED:
            return self._generate_name_based(model_class, **kwargs)
        elif self.pattern == NumberingPattern.PARENT_BASED:
            return self._generate_parent_based(model_class, **kwargs)
        elif self.pattern == NumberingPattern.CUSTOM:
            return kwargs.get('pattern', '')

    def _generate_numeric(self, model_class):
        """توليد رقم تسلسلي"""
        max_value = model_class.objects.aggregate(
            max_value=models.Max('number')
        )['max_value'] or 0

        new_value = max_value + 1
        if new_value > self.max_value:
            raise ValidationError(_('تم تجاوز الحد الأقصى للأرقام المسموح بها'))
        return new_value

    def _generate_alpha(self, model_class):
        """توليد حرف أبجدي"""
        max_value = model_class.objects.aggregate(
            max_value=models.Max('number')
        )['max_value'] or 0

        new_value = max_value + 1
        if new_value > 26:
            raise ValidationError(_('تم تجاوز الحد الأقصى للحروف الأبجدية'))
        return chr(64 + new_value)

    def _generate_alphanumeric(self, model_class, **kwargs):
        """توليد رمز مختلط من حروف وأرقام"""
        prefix = kwargs.get('prefix', 'A')
        max_entry = model_class.objects.filter(
            number__startswith=prefix
        ).aggregate(max_val=models.Max('number'))['max_val']

        if not max_entry:
            return f"{prefix}1"

        current_number = int(max_entry[len(prefix):]) + 1
        return f"{prefix}{current_number}"

    def _generate_name_based(self, model_class, **kwargs):
        """توليد رمز مبني على الاسم"""
        name = kwargs.get('name', '')
        target_field = kwargs.get('field', 'code')

        if not name:
            raise ValidationError(_('الاسم مطلوب لتوليد الكود'))

        words = slugify(name).replace('-', ' ').split()
        base_code = ''.join(
            word[0].upper()
            for word in words
            if word and word.lower() not in self.ignored_words
        )

        # التحقق من وجود الكود
        existing_codes = model_class.objects.filter(**{
            f"{target_field}__startswith": base_code
        }).values_list(target_field, flat=True)

        if base_code not in existing_codes:
            return base_code

        i = 1
        while f"{base_code}{i}" in existing_codes:
            i += 1
        return f"{base_code}{i}"

    def _generate_parent_based(self, model_class, **kwargs):
        """توليد رقم مبني على الكيان الأب"""
        parent_id = kwargs.get('parent_id')
        parent_field = kwargs.get('parent_field')
        target_field = kwargs.get('field', 'number')

        if not parent_id or not parent_field:
            raise ValidationError(_('يجب تحديد parent_id و parent_field'))

        prefix = int(parent_id) * 100

        filter_kwargs = {
            f"{parent_field}_id": parent_id,
            f"{target_field}__gte": prefix,
            f"{target_field}__lt": prefix + 100
        }

        max_value = model_class.objects.filter(**filter_kwargs).aggregate(
            max_value=models.Max(target_field)
        )['max_value'] or prefix

        new_value = max_value + 1
        if new_value >= prefix + 100:
            raise ValidationError(_('تم تجاوز الحد الأقصى داخل هذا الكيان الأبوي'))

        return new_value

    def validate_number(self, number):
        """التحقق من صحة الرقم"""
        try:
            num = int(number)
            if num < self.min_value or num > self.max_value:
                raise ValidationError(
                    _('الرقم يجب أن يكون بين %(min)d و %(max)d') % {
                        'min': self.min_value,
                        'max': self.max_value
                    }
                )
        except (TypeError, ValueError):
            raise ValidationError(_('قيمة الرقم غير صالحة'))

    def format_number(self, number):
        """تنسيق الرقم"""
        formatted = str(number)

        if self.pattern == NumberingPattern.NUMERIC:
            formatted = str(number).zfill(self.padding)

        if self.prefix:
            formatted = f"{self.prefix}{self.separator}{formatted}"

        if self.suffix:
            formatted = f"{formatted}{self.separator}{self.suffix}"

        return formatted
