"""
تسجيل نماذج تطبيق المستخدمين في واجهة الإدارة
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import (
    User, UserProfile, Role, UserRole,
    Student, FacultyMember, StaffMember,
    UserLog, Notification
)


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profile')
    fk_name = 'user'


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1
    verbose_name_plural = _('Roles')
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'national_id', 'birth_date', 'gender', 'phone_number', 'secondary_email', 'profile_picture')}),
        (_('Address'), {'fields': ('address', 'city', 'state', 'country', 'postal_code')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'gender')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'national_id')
    ordering = ('email',)
    inlines = (UserProfileInline, UserRoleInline)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_date', 'assigned_by')
    list_filter = ('role', 'assigned_date')
    search_fields = ('user__username', 'user__email', 'role__name')
    raw_id_fields = ('user', 'role', 'assigned_by')
    date_hierarchy = 'assigned_date'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'status', 'admission_date', 'cgpa', 'total_credits_earned')
    list_filter = ('status', 'admission_date')
    search_fields = ('student_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email')
    raw_id_fields = ('user',)
    date_hierarchy = 'admission_date'
    
    fieldsets = (
        (None, {'fields': ('user', 'student_id', 'status', 'admission_date')}),
        (_('Academic Information'), {'fields': ('cgpa', 'total_credits_earned')}),
        (_('Emergency Contact'), {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')}),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = _('Full Name')
    get_full_name.admin_order_field = 'user__first_name'


@admin.register(FacultyMember)
class FacultyMemberAdmin(admin.ModelAdmin):
    list_display = ('faculty_id', 'get_full_name', 'rank', 'department', 'status', 'hire_date')
    list_filter = ('status', 'rank', 'department', 'hire_date')
    search_fields = ('faculty_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'specialization')
    raw_id_fields = ('user', 'department')
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        (None, {'fields': ('user', 'faculty_id', 'status', 'rank', 'department', 'hire_date')}),
        (_('Academic Information'), {'fields': ('specialization', 'research_interests', 'publications')}),
        (_('Office Information'), {'fields': ('office_location', 'office_hours')}),
        (_('Biography'), {'fields': ('biography',)}),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = _('Full Name')
    get_full_name.admin_order_field = 'user__first_name'


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'get_full_name', 'job_title', 'department', 'status', 'hire_date')
    list_filter = ('status', 'department', 'hire_date')
    search_fields = ('staff_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'job_title')
    raw_id_fields = ('user', 'department', 'supervisor')
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        (None, {'fields': ('user', 'staff_id', 'status', 'job_title', 'department', 'hire_date')}),
        (_('Work Information'), {'fields': ('supervisor', 'office_location', 'work_schedule')}),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = _('Full Name')
    get_full_name.admin_order_field = 'user__first_name'


@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_type', 'timestamp', 'ip_address')
    list_filter = ('log_type', 'timestamp')
    search_fields = ('user__username', 'user__email', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'log_type', 'timestamp', 'ip_address', 'user_agent', 'details')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'priority', 'created_at', 'read')
    list_filter = ('notification_type', 'priority', 'read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'title', 'message', 'notification_type', 'priority')}),
        (_('Status'), {'fields': ('read', 'read_at')}),
        (_('Additional Information'), {'fields': ('link', 'sender', 'created_at')}),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = 0
        for notification in queryset:
            if notification.mark_as_read():
                updated += 1
        self.message_user(request, _('%(count)d notifications marked as read.') % {'count': updated})
    mark_as_read.short_description = _('Mark selected notifications as read')
    
    def mark_as_unread(self, request, queryset):
        updated = 0
        for notification in queryset:
            if notification.mark_as_unread():
                updated += 1
        self.message_user(request, _('%(count)d notifications marked as unread.') % {'count': updated})
    mark_as_unread.short_description = _('Mark selected notifications as unread')
