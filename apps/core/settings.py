"""
نظام إدارة إعدادات النظام باستخدام نظام Django المدمج
"""

from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import json


class SystemSetting(models.Model):
    """
    نموذج إعدادات النظام
    """
    
    SETTING_TYPES = [
        ('general', _('General')),
        ('security', _('Security')),
        ('academic', _('Academic')),
        ('financial', _('Financial')),
        ('notification', _('Notification')),
        ('integration', _('Integration')),
        ('ui', _('User Interface')),
        ('other', _('Other')),
    ]
    
    DATA_TYPES = [
        ('string', _('String')),
        ('integer', _('Integer')),
        ('float', _('Float')),
        ('boolean', _('Boolean')),
        ('json', _('JSON')),
        ('date', _('Date')),
        ('datetime', _('DateTime')),
    ]
    
    key = models.CharField(_('Key'), max_length=100, unique=True)
    value = models.TextField(_('Value'))
    
    data_type = models.CharField(
        _('Data Type'),
        max_length=20,
        choices=DATA_TYPES,
        default='string'
    )
    
    setting_type = models.CharField(
        _('Setting Type'),
        max_length=20,
        choices=SETTING_TYPES,
        default='general'
    )
    
    description = models.TextField(_('Description'), blank=True, null=True)
    
    is_public = models.BooleanField(
        _('Is Public'),
        default=False,
        help_text=_('Whether this setting is accessible to all users')
    )
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_settings',
        verbose_name=_('Updated By')
    )
    
    class Meta:
        verbose_name = _('System Setting')
        verbose_name_plural = _('System Settings')
        ordering = ['setting_type', 'key']
    
    def __str__(self):
        return f"{self.key} ({self.get_setting_type_display()})"
    
    def get_typed_value(self):
        """
        الحصول على القيمة بالنوع المناسب
        """
        if self.data_type == 'string':
            return self.value
        elif self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', 'yes', '1')
        elif self.data_type == 'json':
            return json.loads(self.value)
        elif self.data_type == 'date':
            from django.utils.dateparse import parse_date
            return parse_date(self.value)
        elif self.data_type == 'datetime':
            from django.utils.dateparse import parse_datetime
            return parse_datetime(self.value)
        return self.value
    
    def save(self, *args, **kwargs):
        """
        حفظ الإعداد وإزالة ذاكرة التخزين المؤقت
        """
        super().save(*args, **kwargs)
        
        # إزالة ذاكرة التخزين المؤقت
        cache_key = f"system_setting_{self.key}"
        cache.delete(cache_key)
        
        # إزالة ذاكرة التخزين المؤقت لنوع الإعداد
        cache_key = f"system_settings_{self.setting_type}"
        cache.delete(cache_key)


class SettingsManager:
    """
    مدير إعدادات النظام
    """
    
    @staticmethod
    def get_setting(key, default=None, use_cache=True):
        """
        الحصول على قيمة إعداد
        
        :param key: مفتاح الإعداد
        :param default: القيمة الافتراضية إذا لم يتم العثور على الإعداد
        :param use_cache: استخدام ذاكرة التخزين المؤقت
        :return: قيمة الإعداد
        """
        # التحقق من ذاكرة التخزين المؤقت
        cache_key = f"system_setting_{key}"
        
        if use_cache:
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
        
        try:
            setting = SystemSetting.objects.get(key=key)
            value = setting.get_typed_value()
            
            # تخزين القيمة في ذاكرة التخزين المؤقت
            if use_cache:
                cache.set(cache_key, value, timeout=3600)  # تخزين لمدة ساعة
            
            return value
        except SystemSetting.DoesNotExist:
            return default
    
    @staticmethod
    def set_setting(key, value, data_type=None, setting_type='general', description=None, is_public=False, updated_by=None):
        """
        تعيين قيمة إعداد
        
        :param key: مفتاح الإعداد
        :param value: قيمة الإعداد
        :param data_type: نوع البيانات (اختياري)
        :param setting_type: نوع الإعداد (اختياري)
        :param description: وصف الإعداد (اختياري)
        :param is_public: ما إذا كان الإعداد عامًا (اختياري)
        :param updated_by: المستخدم الذي قام بالتعيين (اختياري)
        :return: كائن SystemSetting
        """
        # تحديد نوع البيانات إذا لم يتم تحديده
        if data_type is None:
            if isinstance(value, str):
                data_type = 'string'
            elif isinstance(value, int):
                data_type = 'integer'
            elif isinstance(value, float):
                data_type = 'float'
            elif isinstance(value, bool):
                data_type = 'boolean'
            elif isinstance(value, dict) or isinstance(value, list):
                data_type = 'json'
                value = json.dumps(value)
            else:
                data_type = 'string'
                value = str(value)
        
        # التحقق مما إذا كان الإعداد موجودًا بالفعل
        setting, created = SystemSetting.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'data_type': data_type,
                'setting_type': setting_type,
                'is_public': is_public,
                'updated_by': updated_by
            }
        )
        
        # تحديث الوصف إذا تم تحديده وكان الإعداد جديدًا
        if description and created:
            setting.description = description
            setting.save(update_fields=['description'])
        
        return setting
    
    @staticmethod
    def delete_setting(key):
        """
        حذف إعداد
        
        :param key: مفتاح الإعداد
        :return: True إذا تم الحذف، False إذا لم يتم العثور على الإعداد
        """
        try:
            setting = SystemSetting.objects.get(key=key)
            setting_type = setting.setting_type
            setting.delete()
            
            # إزالة ذاكرة التخزين المؤقت
            cache_key = f"system_setting_{key}"
            cache.delete(cache_key)
            
            # إزالة ذاكرة التخزين المؤقت لنوع الإعداد
            cache_key = f"system_settings_{setting_type}"
            cache.delete(cache_key)
            
            return True
        except SystemSetting.DoesNotExist:
            return False
    
    @staticmethod
    def get_settings_by_type(setting_type, public_only=False, use_cache=True):
        """
        الحصول على الإعدادات حسب النوع
        
        :param setting_type: نوع الإعداد
        :param public_only: ما إذا كان يجب إرجاع الإعدادات العامة فقط
        :param use_cache: استخدام ذاكرة التخزين المؤقت
        :return: قاموس بالإعدادات
        """
        # التحقق من ذاكرة التخزين المؤقت
        cache_key = f"system_settings_{setting_type}"
        
        if use_cache:
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                # إذا كان public_only صحيحًا، قم بتصفية النتائج
                if public_only:
                    return {k: v for k, v in cached_value.items() if k.startswith('public_')}
                return cached_value
        
        query = models.Q(setting_type=setting_type)
        
        if public_only:
            query &= models.Q(is_public=True)
        
        settings_list = SystemSetting.objects.filter(query)
        
        result = {}
        for setting in settings_list:
            result[setting.key] = setting.get_typed_value()
        
        # تخزين النتيجة في ذاكرة التخزين المؤقت
        if use_cache:
            cache.set(cache_key, result, timeout=3600)  # تخزين لمدة ساعة
        
        return result
    
    @staticmethod
    def get_all_settings(public_only=False):
        """
        الحصول على جميع الإعدادات
        
        :param public_only: ما إذا كان يجب إرجاع الإعدادات العامة فقط
        :return: قاموس بالإعدادات مقسمة حسب النوع
        """
        result = {}
        
        for setting_type, _ in SystemSetting.SETTING_TYPES:
            result[setting_type] = SettingsManager.get_settings_by_type(setting_type, public_only)
        
        return result
