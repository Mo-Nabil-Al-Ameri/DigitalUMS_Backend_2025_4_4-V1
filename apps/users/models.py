"""
نماذج إدارة المستخدمين في النظام
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator, MinLengthValidator
from django.conf import settings
import uuid


class UserManager(BaseUserManager):
    """مدير النموذج المخصص للمستخدمين"""
    
    def create_user(self, email, password=None, **extra_fields):
        """إنشاء وحفظ مستخدم جديد"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """إنشاء وحفظ مستخدم مشرف جديد"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """نموذج المستخدم الأساسي في النظام"""
    
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
    ]
    
    # تعريف المصادقات للحقول
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    
    # الحقول الأساسية
    email = models.EmailField(_('Email Address'), unique=True)
    username = models.CharField(
        _('Username'),
        max_length=150,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    
    # معلومات شخصية إضافية
    national_id = models.CharField(
        _('National ID'),
        max_length=20,
        blank=True,
        null=True,
        unique=True
    )
    birth_date = models.DateField(_('Birth Date'), null=True, blank=True)
    gender = models.CharField(_('Gender'), max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    phone_number = models.CharField(
        _('Phone Number'),
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    secondary_email = models.EmailField(_('Secondary Email'), blank=True, null=True)
    profile_picture = models.ImageField(
        _('Profile Picture'),
        upload_to='profile_pictures/%Y/%m/',
        blank=True,
        null=True
    )
    
    # معلومات العنوان
    address = models.TextField(_('Address'), blank=True, null=True)
    city = models.CharField(_('City'), max_length=100, blank=True, null=True)
    state = models.CharField(_('State/Province'), max_length=100, blank=True, null=True)
    country = models.CharField(_('Country'), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, blank=True, null=True)
    
    # معلومات إضافية للنظام
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Designates whether this user should be treated as active.'),
    )
    date_joined = models.DateTimeField(_('Date Joined'), default=timezone.now)
    last_login_ip = models.GenericIPAddressField(_('Last Login IP'), blank=True, null=True)
    
    # تعيين حقل البريد الإلكتروني كحقل تسجيل الدخول
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    # تعيين مدير النموذج المخصص
    objects = UserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """
        الحصول على الاسم الكامل للمستخدم
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """
        الحصول على الاسم الأول للمستخدم
        """
        return self.first_name
    
    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        إرسال بريد إلكتروني إلى هذا المستخدم
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class UserProfile(models.Model):
    """نموذج الملف الشخصي الإضافي للمستخدم"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    
    bio = models.TextField(_('Biography'), blank=True, null=True)
    website = models.URLField(_('Website'), blank=True, null=True)
    social_media_links = models.JSONField(_('Social Media Links'), blank=True, null=True)
    preferred_language = models.CharField(_('Preferred Language'), max_length=10, blank=True, null=True)
    timezone = models.CharField(_('Timezone'), max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"


class Role(models.Model):
    """نموذج الأدوار في النظام"""
    
    name = models.CharField(_('Role Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('Permissions'),
        blank=True,
        related_name='roles'
    )
    
    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserRole(models.Model):
    """نموذج ربط المستخدمين بالأدوار"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_('User')
    )
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_('Role')
    )
    
    assigned_date = models.DateTimeField(_('Assigned Date'), auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_roles',
        verbose_name=_('Assigned By')
    )
    
    class Meta:
        verbose_name = _('User Role')
        verbose_name_plural = _('User Roles')
        unique_together = ('user', 'role')
        ordering = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class Student(models.Model):
    """نموذج الطالب"""
    
    STUDENT_STATUS = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('graduated', _('Graduated')),
        ('suspended', _('Suspended')),
        ('withdrawn', _('Withdrawn')),
        ('transferred', _('Transferred')),
        ('on_leave', _('On Leave')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student',
        verbose_name=_('User')
    )
    
    student_id = models.CharField(
        _('Student ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique identifier for the student')
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STUDENT_STATUS,
        default='active'
    )
    
    admission_date = models.DateField(_('Admission Date'), default=timezone.now)
    
    # المعلومات الأكاديمية
    cgpa = models.DecimalField(
        _('Cumulative GPA'),
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    
    total_credits_earned = models.PositiveIntegerField(
        _('Total Credits Earned'),
        default=0
    )
    
    # معلومات إضافية
    emergency_contact_name = models.CharField(
        _('Emergency Contact Name'),
        max_length=100,
        blank=True,
        null=True
    )
    
    emergency_contact_phone = models.CharField(
        _('Emergency Contact Phone'),
        max_length=17,
        blank=True,
        null=True
    )
    
    emergency_contact_relationship = models.CharField(
        _('Emergency Contact Relationship'),
        max_length=50,
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Student')
        verbose_name_plural = _('Students')
        ordering = ['student_id']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"
    
    def update_cgpa(self):
        """تحديث المعدل التراكمي للطالب"""
        from apps.academic.models import StudentGrade
        
        grades = StudentGrade.objects.filter(
            student=self,
            grade__isnull=False
        )
        
        if not grades.exists():
            return 0.0
        
        total_points = 0
        total_credits = 0
        
        for grade in grades:
            total_points += grade.grade_points * grade.course.credit_hours
            total_credits += grade.course.credit_hours
        
        if total_credits > 0:
            self.cgpa = round(total_points / total_credits, 2)
        else:
            self.cgpa = 0.0
        
        self.save(update_fields=['cgpa'])
        return self.cgpa
    
    def update_credits_earned(self):
        """تحديث عدد الساعات المكتسبة"""
        from apps.academic.models import StudentGrade
        
        credits = StudentGrade.objects.filter(
            student=self,
            grade__is_passing=True
        ).aggregate(
            total=models.Sum('course__credit_hours')
        )['total'] or 0
        
        self.total_credits_earned = credits
        self.save(update_fields=['total_credits_earned'])
        return self.total_credits_earned


class FacultyMember(models.Model):
    """نموذج عضو هيئة التدريس"""
    
    FACULTY_STATUS = [
        ('active', _('Active')),
        ('on_leave', _('On Leave')),
        ('sabbatical', _('Sabbatical')),
        ('retired', _('Retired')),
        ('terminated', _('Terminated')),
    ]
    
    FACULTY_RANKS = [
        ('professor', _('Professor')),
        ('associate_professor', _('Associate Professor')),
        ('assistant_professor', _('Assistant Professor')),
        ('lecturer', _('Lecturer')),
        ('instructor', _('Instructor')),
        ('adjunct', _('Adjunct Faculty')),
        ('visiting', _('Visiting Faculty')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='faculty',
        verbose_name=_('User')
    )
    
    faculty_id = models.CharField(
        _('Faculty ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique identifier for the faculty member')
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=FACULTY_STATUS,
        default='active'
    )
    
    rank = models.CharField(
        _('Academic Rank'),
        max_length=30,
        choices=FACULTY_RANKS,
        default='instructor'
    )
    
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        related_name='faculty_members',
        verbose_name=_('Department')
    )
    
    hire_date = models.DateField(_('Hire Date'), default=timezone.now)
    
    # معلومات أكاديمية
    specialization = models.CharField(
        _('Specialization'),
        max_length=200,
        blank=True,
        null=True
    )
    
    research_interests = models.TextField(
        _('Research Interests'),
        blank=True,
        null=True
    )
    
    office_location = models.CharField(
        _('Office Location'),
        max_length=100,
        blank=True,
        null=True
    )
    
    office_hours = models.TextField(
        _('Office Hours'),
        blank=True,
        null=True
    )
    
    # معلومات إضافية
    biography = models.TextField(
        _('Biography'),
        blank=True,
        null=True
    )
    
    publications = models.TextField(
        _('Publications'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Faculty Member')
        verbose_name_plural = _('Faculty Members')
        ordering = ['faculty_id']
    
    def __str__(self):
        return f"{self.get_rank_display()} {self.user.get_full_name()} ({self.faculty_id})"
    
    def is_department_head(self):
        """التحقق مما إذا كان عضو هيئة التدريس رئيس قسم"""
        if not self.department:
            return False
        
        return self.department.head == self
    
    def is_dean(self):
        """التحقق مما إذا كان عضو هيئة التدريس عميد كلية"""
        if not self.department or not self.department.college:
            return False
        
        return self.department.college.dean == self


class StaffMember(models.Model):
    """نموذج الموظف الإداري"""
    
    STAFF_STATUS = [
        ('active', _('Active')),
        ('on_leave', _('On Leave')),
        ('terminated', _('Terminated')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name=_('User')
    )
    
    staff_id = models.CharField(
        _('Staff ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique identifier for the staff member')
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STAFF_STATUS,
        default='active'
    )
    
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members',
        verbose_name=_('Department')
    )
    
    job_title = models.CharField(
        _('Job Title'),
        max_length=100
    )
    
    hire_date = models.DateField(_('Hire Date'), default=timezone.now)
    
    # معلومات إضافية
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_staff',
        verbose_name=_('Supervisor')
    )
    
    office_location = models.CharField(
        _('Office Location'),
        max_length=100,
        blank=True,
        null=True
    )
    
    work_schedule = models.TextField(
        _('Work Schedule'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Staff Member')
        verbose_name_plural = _('Staff Members')
        ordering = ['staff_id']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.job_title} ({self.staff_id})"


class UserLog(models.Model):
    """نموذج سجل نشاط المستخدم"""
    
    LOG_TYPES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('password_change', _('Password Change')),
        ('profile_update', _('Profile Update')),
        ('role_change', _('Role Change')),
        ('status_change', _('Status Change')),
        ('other', _('Other')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('User')
    )
    
    log_type = models.CharField(
        _('Log Type'),
        max_length=20,
        choices=LOG_TYPES
    )
    
    timestamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        blank=True,
        null=True
    )
    
    user_agent = models.TextField(_('User Agent'), blank=True, null=True)
    
    details = models.JSONField(_('Details'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('User Log')
        verbose_name_plural = _('User Logs')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_log_type_display()} - {self.timestamp}"


class Notification(models.Model):
    """نموذج الإشعارات للمستخدمين"""
    
    NOTIFICATION_TYPES = [
        ('system', _('System')),
        ('academic', _('Academic')),
        ('enrollment', _('Enrollment')),
        ('grade', _('Grade')),
        ('financial', _('Financial')),
        ('announcement', _('Announcement')),
        ('message', _('Message')),
        ('other', _('Other')),
    ]
    
    NOTIFICATION_PRIORITIES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User')
    )
    
    title = models.CharField(_('Title'), max_length=200)
    
    message = models.TextField(_('Message'))
    
    notification_type = models.CharField(
        _('Notification Type'),
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    
    priority = models.CharField(
        _('Priority'),
        max_length=10,
        choices=NOTIFICATION_PRIORITIES,
        default='medium'
    )
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    read = models.BooleanField(_('Read'), default=False)
    
    read_at = models.DateTimeField(_('Read At'), null=True, blank=True)
    
    link = models.URLField(_('Link'), blank=True, null=True)
    
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name=_('Sender')
    )
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """تعليم الإشعار كمقروء"""
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
            return True
        return False
    
    def mark_as_unread(self):
        """تعليم الإشعار كغير مقروء"""
        if self.read:
            self.read = False
            self.read_at = None
            self.save(update_fields=['read', 'read_at'])
            return True
        return False
