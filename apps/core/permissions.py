"""
نظام الصلاحيات المبني على نظام صلاحيات Django الأساسي
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class RoleManager:
    """
    مدير الأدوار باستخدام نظام المجموعات في Django
    """
    
    @staticmethod
    def create_role(name, permissions=None, description=None):
        """
        إنشاء دور جديد (مجموعة) مع صلاحيات
        
        :param name: اسم الدور
        :param permissions: قائمة بالصلاحيات (اختياري)
        :param description: وصف الدور (اختياري)
        :return: كائن Group
        """
        # إنشاء مجموعة جديدة
        group, created = Group.objects.get_or_create(name=name)
        
        # إضافة الصلاحيات إذا تم تحديدها
        if permissions:
            group.permissions.set(permissions)
        
        return group
    
    @staticmethod
    def get_role(name):
        """
        الحصول على دور (مجموعة) بالاسم
        
        :param name: اسم الدور
        :return: كائن Group أو None
        """
        try:
            return Group.objects.get(name=name)
        except Group.DoesNotExist:
            return None
    
    @staticmethod
    def delete_role(name):
        """
        حذف دور (مجموعة) بالاسم
        
        :param name: اسم الدور
        :return: True إذا تم الحذف، False إذا لم يتم العثور على الدور
        """
        try:
            group = Group.objects.get(name=name)
            group.delete()
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def get_all_roles():
        """
        الحصول على جميع الأدوار (المجموعات)
        
        :return: قائمة بالمجموعات
        """
        return Group.objects.all()
    
    @staticmethod
    def get_role_permissions(role_name):
        """
        الحصول على صلاحيات الدور (المجموعة)
        
        :param role_name: اسم الدور
        :return: قائمة بالصلاحيات
        """
        try:
            group = Group.objects.get(name=role_name)
            return group.permissions.all()
        except Group.DoesNotExist:
            return []
    
    @staticmethod
    def add_permission_to_role(role_name, permission):
        """
        إضافة صلاحية إلى دور (مجموعة)
        
        :param role_name: اسم الدور
        :param permission: الصلاحية
        :return: True إذا تمت الإضافة، False إذا لم يتم العثور على الدور
        """
        try:
            group = Group.objects.get(name=role_name)
            group.permissions.add(permission)
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def remove_permission_from_role(role_name, permission):
        """
        إزالة صلاحية من دور (مجموعة)
        
        :param role_name: اسم الدور
        :param permission: الصلاحية
        :return: True إذا تمت الإزالة، False إذا لم يتم العثور على الدور
        """
        try:
            group = Group.objects.get(name=role_name)
            group.permissions.remove(permission)
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def assign_role_to_user(user, role_name):
        """
        تعيين دور (مجموعة) للمستخدم
        
        :param user: المستخدم
        :param role_name: اسم الدور
        :return: True إذا تم التعيين، False إذا لم يتم العثور على الدور
        """
        try:
            group = Group.objects.get(name=role_name)
            user.groups.add(group)
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def remove_role_from_user(user, role_name):
        """
        إزالة دور (مجموعة) من المستخدم
        
        :param user: المستخدم
        :param role_name: اسم الدور
        :return: True إذا تمت الإزالة، False إذا لم يتم العثور على الدور
        """
        try:
            group = Group.objects.get(name=role_name)
            user.groups.remove(group)
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_roles(user):
        """
        الحصول على أدوار (مجموعات) المستخدم
        
        :param user: المستخدم
        :return: قائمة بالمجموعات
        """
        return user.groups.all()
    
    @staticmethod
    def has_role(user, role_name):
        """
        التحقق مما إذا كان المستخدم لديه دور (مجموعة) معين
        
        :param user: المستخدم
        :param role_name: اسم الدور
        :return: True إذا كان لديه الدور، False إذا لم يكن
        """
        return user.groups.filter(name=role_name).exists()


class PermissionManager:
    """
    مدير الصلاحيات باستخدام نظام الصلاحيات في Django
    """
    
    @staticmethod
    def get_all_permissions():
        """
        الحصول على جميع الصلاحيات
        
        :return: قائمة بالصلاحيات
        """
        return Permission.objects.all()
    
    @staticmethod
    def get_permission_by_codename(codename, app_label=None):
        """
        الحصول على صلاحية بالرمز
        
        :param codename: رمز الصلاحية
        :param app_label: تسمية التطبيق (اختياري)
        :return: كائن Permission أو None
        """
        query = Q(codename=codename)
        
        if app_label:
            query &= Q(content_type__app_label=app_label)
        
        try:
            return Permission.objects.get(query)
        except Permission.DoesNotExist:
            return None
    
    @staticmethod
    def get_permissions_for_model(model):
        """
        الحصول على صلاحيات النموذج
        
        :param model: النموذج
        :return: قائمة بالصلاحيات
        """
        content_type = ContentType.objects.get_for_model(model)
        return Permission.objects.filter(content_type=content_type)
    
    @staticmethod
    def get_user_permissions(user):
        """
        الحصول على جميع صلاحيات المستخدم
        
        :param user: المستخدم
        :return: قائمة بالصلاحيات
        """
        if user.is_superuser:
            # المشرفون لديهم جميع الصلاحيات
            return Permission.objects.all()
        
        # الحصول على الصلاحيات من المجموعات والصلاحيات المباشرة
        return Permission.objects.filter(
            Q(group__user=user) | Q(user=user)
        ).distinct()
    
    @staticmethod
    def has_permission(user, permission_codename, app_label=None):
        """
        التحقق مما إذا كان المستخدم لديه صلاحية معينة
        
        :param user: المستخدم
        :param permission_codename: رمز الصلاحية
        :param app_label: تسمية التطبيق (اختياري)
        :return: True إذا كان لديه الصلاحية، False إذا لم يكن
        """
        # المشرفون لديهم جميع الصلاحيات
        if user.is_superuser:
            return True
        
        # بناء استعلام الصلاحية
        if app_label:
            perm = f"{app_label}.{permission_codename}"
        else:
            perm = permission_codename
        
        # التحقق من صلاحيات المستخدم
        return user.has_perm(perm)
    
    @staticmethod
    def add_permission_to_user(user, permission_codename, app_label=None):
        """
        إضافة صلاحية مباشرة للمستخدم
        
        :param user: المستخدم
        :param permission_codename: رمز الصلاحية
        :param app_label: تسمية التطبيق (اختياري)
        :return: True إذا تمت الإضافة، False إذا لم يتم العثور على الصلاحية
        """
        permission = PermissionManager.get_permission_by_codename(permission_codename, app_label)
        
        if permission:
            user.user_permissions.add(permission)
            return True
        
        return False
    
    @staticmethod
    def remove_permission_from_user(user, permission_codename, app_label=None):
        """
        إزالة صلاحية مباشرة من المستخدم
        
        :param user: المستخدم
        :param permission_codename: رمز الصلاحية
        :param app_label: تسمية التطبيق (اختياري)
        :return: True إذا تمت الإزالة، False إذا لم يتم العثور على الصلاحية
        """
        permission = PermissionManager.get_permission_by_codename(permission_codename, app_label)
        
        if permission:
            user.user_permissions.remove(permission)
            return True
        
        return False


class WorkflowManager:
    """
    مدير سير العمل باستخدام نظام الصلاحيات في Django
    """
    
    @staticmethod
    def check_transition_permission(user, obj, source_state, target_state):
        """
        التحقق من صلاحيات انتقال سير العمل
        
        :param user: المستخدم
        :param obj: الكائن
        :param source_state: الحالة المصدر
        :param target_state: الحالة الهدف
        :return: True إذا كان مسموحًا، False إذا كان غير مسموح
        """
        # المشرفون لديهم جميع الصلاحيات
        if user.is_superuser:
            return True
        
        # الحصول على نوع المحتوى
        content_type = ContentType.objects.get_for_model(obj.__class__)
        
        # بناء رمز الصلاحية
        permission_codename = f"can_transition_{source_state}_to_{target_state}"
        
        # التحقق من صلاحيات المستخدم
        return user.has_perm(f"{content_type.app_label}.{permission_codename}")
    
    @staticmethod
    def apply_transition(user, obj, target_state):
        """
        تطبيق انتقال سير العمل
        
        :param user: المستخدم
        :param obj: الكائن
        :param target_state: الحالة الهدف
        :return: True إذا تم التطبيق بنجاح، False إذا لم يكن مسموحًا
        """
        # التحقق من صلاحيات الانتقال
        source_state = obj.status
        
        if not WorkflowManager.check_transition_permission(user, obj, source_state, target_state):
            return False
        
        # تغيير الحالة
        obj.status = target_state
        obj.save()
        
        # تسجيل انتقال سير العمل (يمكن استخدام نظام التدقيق)
        
        return True


# زخارف للتحقق من الصلاحيات

def permission_required(perm, login_url=None, raise_exception=False):
    """
    زخرفة للتحقق من صلاحيات الوصول للعرض (تستخدم زخرفة Django الأساسية)
    
    :param perm: الصلاحية المطلوبة
    :param login_url: عنوان URL لتسجيل الدخول (اختياري)
    :param raise_exception: ما إذا كان يجب رفع استثناء PermissionDenied (اختياري)
    """
    from django.contrib.auth.decorators import permission_required as django_permission_required
    return django_permission_required(perm, login_url=login_url, raise_exception=raise_exception)


def role_required(role_name, login_url=None, raise_exception=False):
    """
    زخرفة للتحقق من دور المستخدم
    
    :param role_name: اسم الدور المطلوب
    :param login_url: عنوان URL لتسجيل الدخول (اختياري)
    :param raise_exception: ما إذا كان يجب رفع استثناء PermissionDenied (اختياري)
    """
    from django.contrib.auth.decorators import user_passes_test
    from django.core.exceptions import PermissionDenied
    
    def check_role(user):
        if not user.is_authenticated:
            return False
        return user.is_superuser or RoleManager.has_role(user, role_name)
    
    if raise_exception:
        def check_role(user):
            if not user.is_authenticated:
                return False
            if user.is_superuser or RoleManager.has_role(user, role_name):
                return True
            raise PermissionDenied("You do not have the required role.")
    
    return user_passes_test(check_role, login_url=login_url)


def workflow_transition_permission(source_state, target_state, login_url=None, raise_exception=False):
    """
    زخرفة للتحقق من صلاحيات انتقال سير العمل
    
    :param source_state: الحالة المصدر
    :param target_state: الحالة الهدف
    :param login_url: عنوان URL لتسجيل الدخول (اختياري)
    :param raise_exception: ما إذا كان يجب رفع استثناء PermissionDenied (اختياري)
    """
    from django.contrib.auth.decorators import user_passes_test
    from django.core.exceptions import PermissionDenied
    
    def check_transition_permission(user):
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # الحصول على نوع المحتوى (يجب تحديده في العرض)
        view_kwargs = getattr(user, '_view_kwargs', {})
        obj = view_kwargs.get('object', None)
        
        if not obj:
            return False
        
        return WorkflowManager.check_transition_permission(user, obj, source_state, target_state)
    
    if raise_exception:
        def check_transition_permission(user):
            if not user.is_authenticated:
                return False
            
            if user.is_superuser:
                return True
            
            # الحصول على نوع المحتوى (يجب تحديده في العرض)
            view_kwargs = getattr(user, '_view_kwargs', {})
            obj = view_kwargs.get('object', None)
            
            if not obj:
                return False
            
            if WorkflowManager.check_transition_permission(user, obj, source_state, target_state):
                return True
            
            raise PermissionDenied("You do not have permission to perform this transition.")
    
    return user_passes_test(check_transition_permission, login_url=login_url)
