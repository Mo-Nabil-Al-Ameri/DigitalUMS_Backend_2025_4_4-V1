"""
نظام إدارة سير العمل (Workflow) باستخدام نظام Django المدمج
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied

from .audit import AuditLogManager


class WorkflowState(models.Model):
    """
    نموذج حالة سير العمل
    """
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content Type')
    )
    
    name = models.CharField(_('Name'), max_length=100)
    
    code = models.CharField(_('Code'), max_length=50)
    
    description = models.TextField(_('Description'), blank=True, null=True)
    
    is_initial = models.BooleanField(
        _('Is Initial State'),
        default=False,
        help_text=_('Whether this is the initial state for new objects')
    )
    
    is_final = models.BooleanField(
        _('Is Final State'),
        default=False,
        help_text=_('Whether this is a final state (end of workflow)')
    )
    
    order = models.PositiveIntegerField(_('Order'), default=0)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Workflow State')
        verbose_name_plural = _('Workflow States')
        unique_together = ('content_type', 'code')
        ordering = ['content_type', 'order', 'name']
    
    def __str__(self):
        return f"{self.content_type.model}: {self.name} ({self.code})"


class WorkflowTransition(models.Model):
    """
    نموذج انتقال سير العمل
    """
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content Type')
    )
    
    name = models.CharField(_('Name'), max_length=100)
    
    description = models.TextField(_('Description'), blank=True, null=True)
    
    source_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name='source_transitions',
        verbose_name=_('Source State')
    )
    
    target_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name='target_transitions',
        verbose_name=_('Target State')
    )
    
    permission_codename = models.CharField(
        _('Permission Codename'),
        max_length=100,
        help_text=_('Codename of the permission required to perform this transition')
    )
    
    is_automatic = models.BooleanField(
        _('Is Automatic'),
        default=False,
        help_text=_('Whether this transition happens automatically when conditions are met')
    )
    
    conditions = models.JSONField(
        _('Conditions'),
        blank=True,
        null=True,
        help_text=_('Conditions that must be met for automatic transitions')
    )
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Workflow Transition')
        verbose_name_plural = _('Workflow Transitions')
        unique_together = ('content_type', 'source_state', 'target_state')
        ordering = ['content_type', 'source_state', 'target_state']
    
    def __str__(self):
        return f"{self.name}: {self.source_state.name} → {self.target_state.name}"
    
    def has_permission(self, user):
        """
        التحقق مما إذا كان المستخدم لديه صلاحية لهذا الانتقال
        """
        if user.is_superuser:
            return True
        
        app_label = self.content_type.app_label
        return user.has_perm(f"{app_label}.{self.permission_codename}")


class WorkflowLog(models.Model):
    """
    نموذج سجل سير العمل
    """
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Content Type')
    )
    
    object_id = models.CharField(_('Object ID'), max_length=255)
    
    content_object = GenericForeignKey('content_type', 'object_id')
    
    transition = models.ForeignKey(
        WorkflowTransition,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Transition')
    )
    
    from_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name='from_logs',
        verbose_name=_('From State')
    )
    
    to_state = models.ForeignKey(
        WorkflowState,
        on_delete=models.CASCADE,
        related_name='to_logs',
        verbose_name=_('To State')
    )
    
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_logs',
        verbose_name=_('Performed By')
    )
    
    performed_at = models.DateTimeField(_('Performed At'), auto_now_add=True)
    
    comments = models.TextField(_('Comments'), blank=True, null=True)
    
    is_automatic = models.BooleanField(_('Is Automatic'), default=False)
    
    class Meta:
        verbose_name = _('Workflow Log')
        verbose_name_plural = _('Workflow Logs')
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.content_type.model} ({self.object_id}): {self.from_state.name} → {self.to_state.name}"


class WorkflowManager:
    """
    مدير سير العمل
    """
    
    @staticmethod
    def get_workflow_states(content_type):
        """
        الحصول على حالات سير العمل لنوع محتوى
        
        :param content_type: نوع المحتوى
        :return: قائمة بحالات سير العمل
        """
        return WorkflowState.objects.filter(content_type=content_type).order_by('order')
    
    @staticmethod
    def get_initial_state(content_type):
        """
        الحصول على الحالة الأولية لنوع محتوى
        
        :param content_type: نوع المحتوى
        :return: حالة سير العمل الأولية
        """
        try:
            return WorkflowState.objects.get(content_type=content_type, is_initial=True)
        except WorkflowState.DoesNotExist:
            return None
    
    @staticmethod
    def get_available_transitions(obj, user=None):
        """
        الحصول على الانتقالات المتاحة للكائن
        
        :param obj: الكائن
        :param user: المستخدم (اختياري)
        :return: قائمة بالانتقالات المتاحة
        """
        content_type = ContentType.objects.get_for_model(obj.__class__)
        
        # الحصول على الحالة الحالية للكائن
        current_state_code = getattr(obj, 'status', None)
        
        if not current_state_code:
            return []
        
        try:
            current_state = WorkflowState.objects.get(content_type=content_type, code=current_state_code)
        except WorkflowState.DoesNotExist:
            return []
        
        # الحصول على الانتقالات من الحالة الحالية
        transitions = WorkflowTransition.objects.filter(
            content_type=content_type,
            source_state=current_state
        )
        
        # إذا تم تحديد المستخدم، تحقق من الصلاحيات
        if user:
            return [t for t in transitions if t.has_permission(user)]
        
        return transitions
    
    @staticmethod
    def can_transition(obj, target_state_code, user):
        """
        التحقق مما إذا كان يمكن الانتقال إلى حالة معينة
        
        :param obj: الكائن
        :param target_state_code: رمز الحالة الهدف
        :param user: المستخدم
        :return: True إذا كان يمكن الانتقال، False إذا لم يكن
        """
        content_type = ContentType.objects.get_for_model(obj.__class__)
        
        # الحصول على الحالة الحالية للكائن
        current_state_code = getattr(obj, 'status', None)
        
        if not current_state_code:
            return False
        
        try:
            current_state = WorkflowState.objects.get(content_type=content_type, code=current_state_code)
            target_state = WorkflowState.objects.get(content_type=content_type, code=target_state_code)
        except WorkflowState.DoesNotExist:
            return False
        
        # البحث عن الانتقال المناسب
        try:
            transition = WorkflowTransition.objects.get(
                content_type=content_type,
                source_state=current_state,
                target_state=target_state
            )
        except WorkflowTransition.DoesNotExist:
            return False
        
        # التحقق من صلاحيات المستخدم
        return transition.has_permission(user)
    
    @staticmethod
    def transition(obj, target_state_code, user, comments=None):
        """
        الانتقال إلى حالة معينة
        
        :param obj: الكائن
        :param target_state_code: رمز الحالة الهدف
        :param user: المستخدم
        :param comments: تعليقات (اختياري)
        :return: True إذا تم الانتقال بنجاح، False إذا لم يكن
        """
        content_type = ContentType.objects.get_for_model(obj.__class__)
        
        # الحصول على الحالة الحالية للكائن
        current_state_code = getattr(obj, 'status', None)
        
        if not current_state_code:
            return False
        
        try:
            current_state = WorkflowState.objects.get(content_type=content_type, code=current_state_code)
            target_state = WorkflowState.objects.get(content_type=content_type, code=target_state_code)
        except WorkflowState.DoesNotExist:
            return False
        
        # البحث عن الانتقال المناسب
        try:
            transition = WorkflowTransition.objects.get(
                content_type=content_type,
                source_state=current_state,
                target_state=target_state
            )
        except WorkflowTransition.DoesNotExist:
            return False
        
        # التحقق من صلاحيات المستخدم
        if not transition.has_permission(user):
            raise PermissionDenied("You do not have permission to perform this transition.")
        
        # تغيير الحالة
        setattr(obj, 'status', target_state_code)
        obj.save()
        
        # تسجيل الانتقال
        WorkflowLog.objects.create(
            content_type=content_type,
            object_id=obj.pk,
            transition=transition,
            from_state=current_state,
            to_state=target_state,
            performed_by=user,
            comments=comments,
            is_automatic=False
        )
        
        # تسجيل الانتقال في سجل التدقيق
        AuditLogManager.log_change(
            user=user,
            obj=obj,
            message=f"Changed status from {current_state.name} to {target_state.name}",
            changed_data={'status': target_state_code}
        )
        
        return True
    
    @staticmethod
    def get_workflow_history(obj):
        """
        الحصول على سجل سير العمل للكائن
        
        :param obj: الكائن
        :return: قائمة بسجلات سير العمل
        """
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return WorkflowLog.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).order_by('-performed_at')
    
    @staticmethod
    def check_automatic_transitions():
        """
        التحقق من الانتقالات التلقائية
        
        :return: عدد الانتقالات التي تم تنفيذها
        """
        # الحصول على جميع الانتقالات التلقائية
        automatic_transitions = WorkflowTransition.objects.filter(is_automatic=True)
        
        count = 0
        
        for transition in automatic_transitions:
            content_type = transition.content_type
            model = content_type.model_class()
            
            # الحصول على الكائنات في الحالة المصدر
            source_state_code = transition.source_state.code
            objects = model.objects.filter(status=source_state_code)
            
            for obj in objects:
                # التحقق من الشروط
                if transition.conditions:
                    # تنفيذ الشروط (يمكن تحسين هذا)
                    conditions_met = True
                    
                    for field, condition in transition.conditions.items():
                        field_value = getattr(obj, field, None)
                        
                        if condition.get('type') == 'equals':
                            if field_value != condition.get('value'):
                                conditions_met = False
                                break
                        elif condition.get('type') == 'not_equals':
                            if field_value == condition.get('value'):
                                conditions_met = False
                                break
                        elif condition.get('type') == 'greater_than':
                            if field_value <= condition.get('value'):
                                conditions_met = False
                                break
                        elif condition.get('type') == 'less_than':
                            if field_value >= condition.get('value'):
                                conditions_met = False
                                break
                        # يمكن إضافة المزيد من أنواع الشروط
                    
                    if not conditions_met:
                        continue
                
                # تنفيذ الانتقال
                target_state_code = transition.target_state.code
                setattr(obj, 'status', target_state_code)
                obj.save()
                
                # تسجيل الانتقال
                WorkflowLog.objects.create(
                    content_type=content_type,
                    object_id=obj.pk,
                    transition=transition,
                    from_state=transition.source_state,
                    to_state=transition.target_state,
                    performed_by=None,
                    comments="Automatic transition",
                    is_automatic=True
                )
                
                count += 1
        
        return count


# زخارف للتحقق من صلاحيات سير العمل

def workflow_transition_required(target_state_code, login_url=None, raise_exception=True):
    """
    زخرفة للتحقق من صلاحيات انتقال سير العمل
    
    :param target_state_code: رمز الحالة الهدف
    :param login_url: عنوان URL لتسجيل الدخول (اختياري)
    :param raise_exception: ما إذا كان يجب رفع استثناء PermissionDenied (اختياري)
    """
    from django.contrib.auth.decorators import user_passes_test
    
    def check_transition_permission(user):
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # الحصول على الكائن من العرض
        from django.urls import resolve
        from django.http import Http404
        
        request = getattr(user, '_request', None)
        
        if not request:
            return False
        
        try:
            resolver_match = resolve(request.path)
            view_kwargs = resolver_match.kwargs
            
            # الحصول على الكائن
            model = None
            obj = None
            
            # محاولة الحصول على الكائن من المعرف
            if 'pk' in view_kwargs:
                # الحصول على النموذج من العرض
                view_func = resolver_match.func
                model = getattr(view_func, 'model', None)
                
                if model:
                    try:
                        obj = model.objects.get(pk=view_kwargs['pk'])
                    except model.DoesNotExist:
                        raise Http404("Object not found")
            
            if not obj:
                return False
            
            # التحقق من صلاحيات الانتقال
            return WorkflowManager.can_transition(obj, target_state_code, user)
        except:
            return False
    
    return user_passes_test(check_transition_permission, login_url=login_url, raise_exception=raise_exception)
