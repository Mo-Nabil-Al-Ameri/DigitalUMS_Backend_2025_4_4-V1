"""
إشارات تطبيق المستخدمين
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import user_logged_in, user_logged_out
from django.contrib.auth.signals import user_login_failed

from .models import User, UserProfile, UserLog


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء ملف شخصي للمستخدم عند إنشاء مستخدم جديد"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """حفظ ملف المستخدم الشخصي عند حفظ المستخدم"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # إذا لم يكن لديه ملف شخصي، قم بإنشاء واحد
        UserProfile.objects.create(user=instance)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """تسجيل تسجيل دخول المستخدم"""
    if request and hasattr(request, 'META'):
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        
        # تحديث آخر عنوان IP لتسجيل الدخول
        user.last_login_ip = ip_address
        user.save(update_fields=['last_login_ip'])
        
        # إنشاء سجل تسجيل الدخول
        UserLog.objects.create(
            user=user,
            log_type='login',
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                'session_key': request.session.session_key,
                'timestamp': timezone.now().isoformat()
            }
        )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """تسجيل تسجيل خروج المستخدم"""
    if user and request and hasattr(request, 'META'):
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        
        # إنشاء سجل تسجيل الخروج
        UserLog.objects.create(
            user=user,
            log_type='logout',
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                'session_key': request.session.session_key,
                'timestamp': timezone.now().isoformat()
            }
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """تسجيل فشل تسجيل دخول المستخدم"""
    if request and hasattr(request, 'META'):
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        
        # محاولة العثور على المستخدم
        username = credentials.get('username', None)
        email = credentials.get('email', None)
        
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        
        if username and not user:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass
        
        # إنشاء سجل فشل تسجيل الدخول
        if user:
            UserLog.objects.create(
                user=user,
                log_type='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    'timestamp': timezone.now().isoformat(),
                    'reason': 'Invalid password'
                }
            )
