"""
نظام التدقيق (Audit) باستخدام نظام Django المدمج
"""

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import threading
import json

# متغير محلي للموجه لتخزين كائن الطلب الحالي
_thread_locals = threading.local()


def get_current_user():
    """
    الحصول على المستخدم الحالي من الموجه المحلي
    """
    return getattr(_thread_locals, 'user', None)


def get_client_ip():
    """
    الحصول على عنوان IP للعميل من الموجه المحلي
    """
    request = getattr(_thread_locals, 'request', None)
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    return None


class AuditMiddleware:
    """
    وسيط لتخزين كائن الطلب والمستخدم الحالي في الموجه المحلي
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # تخزين كائن الطلب والمستخدم الحالي
        _thread_locals.request = request
        _thread_locals.user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        response = self.get_response(request)
        
        # إزالة كائن الطلب والمستخدم من الموجه المحلي
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        
        return response


class AuditLogManager:
    """
    مدير سجل التدقيق باستخدام نظام LogEntry في Django
    """
    
    @staticmethod
    def log_addition(user, obj, message=None):
        """
        تسجيل إضافة كائن
        
        :param user: المستخدم
        :param obj: الكائن
        :param message: رسالة (اختياري)
        :return: كائن LogEntry
        """
        if not user:
            user = get_current_user()
        
        if not user:
            return None
        
        if not message:
            message = f"Added {obj.__class__.__name__}: {str(obj)}"
        
        return LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=force_str(obj),
            action_flag=ADDITION,
            change_message=message
        )
    
    @staticmethod
    def log_change(user, obj, message=None, changed_data=None):
        """
        تسجيل تغيير كائن
        
        :param user: المستخدم
        :param obj: الكائن
        :param message: رسالة (اختياري)
        :param changed_data: البيانات المتغيرة (اختياري)
        :return: كائن LogEntry
        """
        if not user:
            user = get_current_user()
        
        if not user:
            return None
        
        if not message:
            message = f"Changed {obj.__class__.__name__}: {str(obj)}"
        
        if changed_data:
            if isinstance(changed_data, dict):
                message = json.dumps([{'changed': {'fields': list(changed_data.keys())}}])
            else:
                message = json.dumps([{'changed': {'fields': changed_data}}])
        
        return LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=force_str(obj),
            action_flag=CHANGE,
            change_message=message
        )
    
    @staticmethod
    def log_deletion(user, obj, message=None):
        """
        تسجيل حذف كائن
        
        :param user: المستخدم
        :param obj: الكائن
        :param message: رسالة (اختياري)
        :return: كائن LogEntry
        """
        if not user:
            user = get_current_user()
        
        if not user:
            return None
        
        if not message:
            message = f"Deleted {obj.__class__.__name__}: {str(obj)}"
        
        return LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=force_str(obj),
            action_flag=DELETION,
            change_message=message
        )
    
    @staticmethod
    def get_object_history(obj):
        """
        الحصول على سجل تغييرات الكائن
        
        :param obj: الكائن
        :return: قائمة بسجلات التغييرات
        """
        content_type = ContentType.objects.get_for_model(obj)
        return LogEntry.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).order_by('-action_time')
    
    @staticmethod
    def get_user_actions(user):
        """
        الحصول على سجل إجراءات المستخدم
        
        :param user: المستخدم
        :return: قائمة بسجلات الإجراءات
        """
        return LogEntry.objects.filter(user=user).order_by('-action_time')


# إشارات لتسجيل التغييرات تلقائيًا

@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """
    تسجيل التغييرات في النماذج
    """
    # تجاهل بعض النماذج الأساسية التي لا تحتاج إلى تتبع
    ignored_models = [
        LogEntry,
        ContentType,
        'django.contrib.sessions.models.Session',
    ]
    
    if sender in ignored_models or sender.__name__ in [m.__name__ for m in ignored_models if hasattr(m, '__name__')]:
        return
    
    # تجاهل النماذج المستثناة في الإعدادات
    excluded_models = getattr(settings, 'AUDIT_EXCLUDED_MODELS', [])
    if sender.__module__ + '.' + sender.__name__ in excluded_models:
        return
    
    # الحصول على المستخدم الحالي
    user = get_current_user()
    
    if not user:
        return
    
    # تسجيل الإجراء
    if created:
        AuditLogManager.log_addition(user, instance)
    else:
        # يمكن تحسين هذا لتتبع الحقول المتغيرة
        AuditLogManager.log_change(user, instance)


@receiver(post_delete)
def log_model_deletion(sender, instance, **kwargs):
    """
    تسجيل حذف النماذج
    """
    # تجاهل بعض النماذج الأساسية التي لا تحتاج إلى تتبع
    ignored_models = [
        LogEntry,
        ContentType,
        'django.contrib.sessions.models.Session',
    ]
    
    if sender in ignored_models or sender.__name__ in [m.__name__ for m in ignored_models if hasattr(m, '__name__')]:
        return
    
    # تجاهل النماذج المستثناة في الإعدادات
    excluded_models = getattr(settings, 'AUDIT_EXCLUDED_MODELS', [])
    if sender.__module__ + '.' + sender.__name__ in excluded_models:
        return
    
    # الحصول على المستخدم الحالي
    user = get_current_user()
    
    if not user:
        return
    
    # تسجيل الإجراء
    AuditLogManager.log_deletion(user, instance)


# زخارف للتسجيل اليدوي

def audit_view(action_type):
    """
    زخرفة لتسجيل إجراءات العرض
    
    :param action_type: نوع الإجراء (view, list, export, etc.)
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            # تسجيل الإجراء فقط إذا كان المستخدم مصادقًا
            if request.user.is_authenticated:
                # محاولة الحصول على اسم العرض
                view_name = view_func.__name__
                
                # تسجيل الإجراء
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=None,
                    object_id=None,
                    object_repr=view_name,
                    action_flag=CHANGE,
                    change_message=f"{action_type} - {request.path}"
                )
            
            return response
        
        return wrapped_view
    
    return decorator
