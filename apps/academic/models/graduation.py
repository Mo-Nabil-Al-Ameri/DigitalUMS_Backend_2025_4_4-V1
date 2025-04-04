"""
نماذج التخرج ومتطلباته
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count, Q


class GraduationApplication(models.Model):
    """نموذج طلب التخرج"""
    
    APPLICATION_STATUS = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('canceled', _('Canceled')),
    ]
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='graduation_applications',
        verbose_name=_("Student")
    )
    
    program = models.ForeignKey(
        'departments.AcademicProgram',
        on_delete=models.CASCADE,
        related_name='graduation_applications',
        verbose_name=_("Academic Program")
    )
    
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        related_name='graduation_applications',
        verbose_name=_("Academic Year")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='graduation_applications',
        verbose_name=_("Semester")
    )
    
    application_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Application Date")
    )
    
    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default='draft',
        verbose_name=_("Status")
    )
    
    expected_graduation_date = models.DateField(
        verbose_name=_("Expected Graduation Date")
    )
    
    actual_graduation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Actual Graduation Date")
    )
    
    reviewer = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_graduation_applications',
        verbose_name=_("Reviewer")
    )
    
    review_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Review Date")
    )
    
    decision_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Decision Date")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Graduation Application")
        verbose_name_plural = _("Graduation Applications")
        ordering = ['-application_date']
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.program.name} ({self.get_status_display()})"
    
    def submit(self):
        """تقديم طلب التخرج"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.save()
            
            # إنشاء فحص متطلبات التخرج
            GraduationRequirementCheck.create_for_application(self)
            return True
        return False
    
    def start_review(self, reviewer):
        """بدء مراجعة طلب التخرج"""
        if self.status == 'submitted':
            self.status = 'under_review'
            self.reviewer = reviewer
            self.review_date = timezone.now()
            self.save()
            return True
        return False
    
    def approve(self):
        """الموافقة على طلب التخرج"""
        if self.status in ['submitted', 'under_review']:
            self.status = 'approved'
            self.decision_date = timezone.now()
            self.actual_graduation_date = self.expected_graduation_date
            self.save()
            
            # تحديث حالة الطالب
            enrollment = self.student.enrollments.get(program=self.program)
            enrollment.graduate()
            
            return True
        return False
    
    def reject(self, reason=None):
        """رفض طلب التخرج"""
        if self.status in ['submitted', 'under_review']:
            self.status = 'rejected'
            self.decision_date = timezone.now()
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Rejected: {reason}"
            self.save()
            return True
        return False
    
    def cancel(self, reason=None):
        """إلغاء طلب التخرج"""
        if self.status not in ['approved', 'rejected', 'canceled']:
            self.status = 'canceled'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Canceled: {reason}"
            self.save()
            return True
        return False
    
    def check_eligibility(self):
        """التحقق من أهلية الطالب للتخرج"""
        # الحصول على فحص متطلبات التخرج
        try:
            check = self.requirement_check
            return check.is_eligible()
        except GraduationRequirementCheck.DoesNotExist:
            # إنشاء فحص جديد
            check = GraduationRequirementCheck.create_for_application(self)
            return check.is_eligible()


class GraduationRequirementCheck(models.Model):
    """نموذج فحص متطلبات التخرج"""
    
    application = models.OneToOneField(
        'GraduationApplication',
        on_delete=models.CASCADE,
        related_name='requirement_check',
        verbose_name=_("Graduation Application")
    )
    
    check_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Check Date")
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated")
    )
    
    total_credits_required = models.PositiveIntegerField(
        verbose_name=_("Total Credits Required")
    )
    
    total_credits_completed = models.PositiveIntegerField(
        verbose_name=_("Total Credits Completed")
    )
    
    min_cgpa_required = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name=_("Minimum CGPA Required")
    )
    
    current_cgpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name=_("Current CGPA")
    )
    
    all_required_courses_completed = models.BooleanField(
        default=False,
        verbose_name=_("All Required Courses Completed")
    )
    
    all_course_groups_requirements_met = models.BooleanField(
        default=False,
        verbose_name=_("All Course Groups Requirements Met")
    )
    
    has_active_academic_warnings = models.BooleanField(
        default=False,
        verbose_name=_("Has Active Academic Warnings")
    )
    
    has_financial_holds = models.BooleanField(
        default=False,
        verbose_name=_("Has Financial Holds")
    )
    
    is_eligible = models.BooleanField(
        default=False,
        verbose_name=_("Is Eligible for Graduation")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Graduation Requirement Check")
        verbose_name_plural = _("Graduation Requirement Checks")
        
    def __str__(self):
        return f"Graduation Check for {self.application.student.user.get_full_name()}"
    
    @classmethod
    def create_for_application(cls, application):
        """إنشاء فحص متطلبات التخرج لطلب تخرج"""
        student = application.student
        program = application.program
        
        # الحصول على إعدادات البرنامج
        program_settings = program.settings
        
        # حساب الساعات المطلوبة والمكتملة
        total_credits_required = program.total_credit_hours
        
        from academic.models import StudentGrade
        completed_credits = StudentGrade.objects.filter(
            student=student,
            grade__is_passing=True
        ).aggregate(
            total=Sum('course__credit_hours')
        )['total'] or 0
        
        # التحقق من إكمال المقررات المطلوبة
        required_courses = program.required_courses.all()
        completed_required_courses = StudentGrade.objects.filter(
            student=student,
            course__in=required_courses,
            grade__is_passing=True
        ).values_list('course__id', flat=True)
        
        all_required_completed = len(completed_required_courses) == required_courses.count()
        
        # التحقق من متطلبات مجموعات المقررات
        course_groups = program.study_plans.first().course_groups.all()
        all_groups_met = True
        
        for group in course_groups:
            completed_in_group = StudentGrade.objects.filter(
                student=student,
                course__course_groups=group,
                grade__is_passing=True
            ).aggregate(
                total=Sum('course__credit_hours')
            )['total'] or 0
            
            if completed_in_group < group.required_credits:
                all_groups_met = False
                break
        
        # التحقق من الإنذارات الأكاديمية
        from academic.models import AcademicWarning
        has_warnings = AcademicWarning.objects.filter(
            student=student,
            status='active'
        ).exists()
        
        # التحقق من المستحقات المالية (افتراضياً لا توجد)
        has_financial_holds = False
        
        # تحديد الأهلية للتخرج
        is_eligible = (
            completed_credits >= total_credits_required and
            student.cgpa >= program_settings.min_cgpa_required and
            all_required_completed and
            all_groups_met and
            not has_warnings and
            not has_financial_holds
        )
        
        # إنشاء فحص متطلبات التخرج
        check = cls.objects.create(
            application=application,
            total_credits_required=total_credits_required,
            total_credits_completed=completed_credits,
            min_cgpa_required=program_settings.min_cgpa_required,
            current_cgpa=student.cgpa,
            all_required_courses_completed=all_required_completed,
            all_course_groups_requirements_met=all_groups_met,
            has_active_academic_warnings=has_warnings,
            has_financial_holds=has_financial_holds,
            is_eligible=is_eligible
        )
        
        # إضافة ملاحظات حول المتطلبات غير المكتملة
        notes = []
        
        if completed_credits < total_credits_required:
            notes.append(f"الساعات المكتملة ({completed_credits}) أقل من المطلوبة ({total_credits_required})")
        
        if student.cgpa < program_settings.min_cgpa_required:
            notes.append(f"المعدل التراكمي ({student.cgpa}) أقل من المطلوب ({program_settings.min_cgpa_required})")
        
        if not all_required_completed:
            missing_courses = required_courses.exclude(id__in=completed_required_courses)
            notes.append(f"المقررات المطلوبة غير المكتملة: {', '.join([c.name for c in missing_courses])}")
        
        if not all_groups_met:
            for group in course_groups:
                completed_in_group = StudentGrade.objects.filter(
                    student=student,
                    course__course_groups=group,
                    grade__is_passing=True
                ).aggregate(
                    total=Sum('course__credit_hours')
                )['total'] or 0
                
                if completed_in_group < group.required_credits:
                    notes.append(f"متطلبات مجموعة {group.name} غير مكتملة: {completed_in_group}/{group.required_credits}")
        
        if has_warnings:
            warnings = AcademicWarning.objects.filter(
                student=student,
                status='active'
            )
            notes.append(f"توجد إنذارات أكاديمية نشطة: {', '.join([w.get_warning_type_display() for w in warnings])}")
        
        if has_financial_holds:
            notes.append("توجد مستحقات مالية غير مسددة")
        
        if notes:
            check.notes = "\n".join(notes)
            check.save(update_fields=['notes'])
        
        return check
    
    def update_check(self):
        """تحديث فحص متطلبات التخرج"""
        # إعادة إنشاء الفحص
        new_check = self.__class__.create_for_application(self.application)
        
        # تحديث الحقول
        self.total_credits_completed = new_check.total_credits_completed
        self.current_cgpa = new_check.current_cgpa
        self.all_required_courses_completed = new_check.all_required_courses_completed
        self.all_course_groups_requirements_met = new_check.all_course_groups_requirements_met
        self.has_active_academic_warnings = new_check.has_active_academic_warnings
        self.has_financial_holds = new_check.has_financial_holds
        self.is_eligible = new_check.is_eligible
        self.notes = new_check.notes
        self.save()
        
        # حذف الفحص الجديد
        new_check.delete()
        
        return self.is_eligible
