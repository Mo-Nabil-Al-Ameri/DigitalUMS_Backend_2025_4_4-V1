"""
نماذج الإرشاد الأكاديمي
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class AcademicAdvisor(models.Model):
    """نموذج المرشد الأكاديمي"""
    
    faculty_member = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.CASCADE,
        related_name='advisor_assignments',
        verbose_name=_("Faculty Member")
    )
    
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='academic_advisors',
        verbose_name=_("Department")
    )
    
    max_students = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Maximum Number of Students")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active")
    )
    
    start_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Start Date")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Academic Advisor")
        verbose_name_plural = _("Academic Advisors")
        unique_together = [['faculty_member', 'department']]
        
    def __str__(self):
        return f"{self.faculty_member.user.get_full_name()} - {self.department.name}"
    
    def get_current_students_count(self):
        """الحصول على عدد الطلاب الحاليين"""
        from academic.models import StudentEnrollment
        
        return StudentEnrollment.objects.filter(
            advisor=self.faculty_member,
            status='active'
        ).count()
    
    def has_capacity(self):
        """التحقق مما إذا كان المرشد لديه سعة لطلاب إضافيين"""
        return self.get_current_students_count() < self.max_students
    
    def get_students(self):
        """الحصول على قائمة الطلاب"""
        from academic.models import StudentEnrollment
        
        return StudentEnrollment.objects.filter(
            advisor=self.faculty_member,
            status='active'
        )
    
    def deactivate(self, reason=None):
        """إلغاء تنشيط المرشد"""
        self.is_active = False
        self.end_date = timezone.now().date()
        if reason:
            self.notes = f"{self.notes}\n[{timezone.now().date()}] Deactivated: {reason}"
        self.save()
        return True


class AdvisingSession(models.Model):
    """نموذج جلسة الإرشاد الأكاديمي"""
    
    SESSION_TYPES = [
        ('registration', _('Registration Advising')),
        ('academic_progress', _('Academic Progress')),
        ('graduation_check', _('Graduation Check')),
        ('career', _('Career Advising')),
        ('general', _('General Advising')),
    ]
    
    SESSION_STATUS = [
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('canceled', _('Canceled')),
        ('no_show', _('No Show')),
    ]
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='advising_sessions',
        verbose_name=_("Student")
    )
    
    advisor = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.CASCADE,
        related_name='advising_sessions',
        verbose_name=_("Advisor")
    )
    
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPES,
        verbose_name=_("Session Type")
    )
    
    scheduled_date = models.DateTimeField(
        verbose_name=_("Scheduled Date")
    )
    
    duration_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Duration (Minutes)")
    )
    
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS,
        default='scheduled',
        verbose_name=_("Status")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    recommendations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Recommendations")
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created Date")
    )
    
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed Date")
    )
    
    class Meta:
        verbose_name = _("Advising Session")
        verbose_name_plural = _("Advising Sessions")
        ordering = ['-scheduled_date']
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_session_type_display()} ({self.scheduled_date.strftime('%Y-%m-%d %H:%M')})"
    
    def complete(self, notes=None, recommendations=None):
        """إكمال جلسة الإرشاد"""
        if self.status == 'scheduled':
            self.status = 'completed'
            self.completed_date = timezone.now()
            
            if notes:
                self.notes = notes
                
            if recommendations:
                self.recommendations = recommendations
                
            self.save()
            return True
        return False
    
    def cancel(self, reason=None):
        """إلغاء جلسة الإرشاد"""
        if self.status == 'scheduled':
            self.status = 'canceled'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Canceled: {reason}"
            self.save()
            return True
        return False
    
    def mark_no_show(self):
        """تعليم الطالب كمتغيب عن الجلسة"""
        if self.status == 'scheduled' and timezone.now() > self.scheduled_date:
            self.status = 'no_show'
            self.save()
            return True
        return False


class AcademicWarning(models.Model):
    """نموذج الإنذار الأكاديمي"""
    
    WARNING_TYPES = [
        ('gpa', _('Low GPA')),
        ('attendance', _('Poor Attendance')),
        ('academic_integrity', _('Academic Integrity Violation')),
        ('course_failure', _('Course Failure')),
        ('probation', _('Academic Probation')),
        ('final_warning', _('Final Warning')),
    ]
    
    WARNING_STATUS = [
        ('active', _('Active')),
        ('resolved', _('Resolved')),
        ('expired', _('Expired')),
    ]
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='academic_warnings',
        verbose_name=_("Student")
    )
    
    warning_type = models.CharField(
        max_length=20,
        choices=WARNING_TYPES,
        verbose_name=_("Warning Type")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='academic_warnings',
        verbose_name=_("Semester")
    )
    
    issue_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Issue Date")
    )
    
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expiry Date")
    )
    
    status = models.CharField(
        max_length=20,
        choices=WARNING_STATUS,
        default='active',
        verbose_name=_("Status")
    )
    
    reason = models.TextField(
        verbose_name=_("Reason")
    )
    
    issued_by = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_warnings',
        verbose_name=_("Issued By")
    )
    
    resolution_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Resolution Date")
    )
    
    resolution_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Resolution Notes")
    )
    
    class Meta:
        verbose_name = _("Academic Warning")
        verbose_name_plural = _("Academic Warnings")
        ordering = ['-issue_date']
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.get_warning_type_display()} ({self.semester})"
    
    def resolve(self, notes=None):
        """حل الإنذار الأكاديمي"""
        if self.status == 'active':
            self.status = 'resolved'
            self.resolution_date = timezone.now().date()
            
            if notes:
                self.resolution_notes = notes
                
            self.save()
            return True
        return False
    
    def check_expiry(self):
        """التحقق من انتهاء صلاحية الإنذار"""
        if self.status == 'active' and self.expiry_date and timezone.now().date() > self.expiry_date:
            self.status = 'expired'
            self.save()
            return True
        return False
    
    @classmethod
    def check_all_expiries(cls):
        """التحقق من انتهاء صلاحية جميع الإنذارات النشطة"""
        today = timezone.now().date()
        expired_warnings = cls.objects.filter(
            status='active',
            expiry_date__lt=today
        )
        
        for warning in expired_warnings:
            warning.status = 'expired'
            warning.save()
            
        return expired_warnings.count()
