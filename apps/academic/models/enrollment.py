"""
نماذج تسجيل الطلاب في البرامج والفصول الدراسية والمقررات
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum


class StudentEnrollment(models.Model):
    """نموذج تسجيل الطالب في البرنامج"""
    
    ENROLLMENT_STATUS = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('active', _('Active')),
        ('on_hold', _('On Hold')),
        ('graduated', _('Graduated')),
        ('withdrawn', _('Withdrawn')),
        ('dismissed', _('Dismissed')),
    ]
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_("Student")
    )
    
    program = models.ForeignKey(
        'departments.AcademicProgram',
        on_delete=models.CASCADE,
        related_name='student_enrollments',
        verbose_name=_("Academic Program")
    )
    
    study_plan = models.ForeignKey(
        'departments.StudyPlan',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        verbose_name=_("Study Plan")
    )
    
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        related_name='student_enrollments',
        verbose_name=_("Academic Year")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='student_enrollments',
        verbose_name=_("Semester")
    )
    
    enrollment_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Enrollment Date")
    )
    
    status = models.CharField(
        max_length=20,
        choices=ENROLLMENT_STATUS,
        default='pending',
        verbose_name=_("Status")
    )
    
    advisor = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advised_students',
        verbose_name=_("Academic Advisor")
    )
    
    expected_graduation = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expected Graduation")
    )
    
    actual_graduation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Actual Graduation Date")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Student Enrollment")
        verbose_name_plural = _("Student Enrollments")
        unique_together = [['student', 'program']]
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.program.name}"
    
    def activate(self):
        """تنشيط التسجيل"""
        if self.status in ['pending', 'approved', 'on_hold']:
            self.status = 'active'
            self.save()
            return True
        return False
    
    def put_on_hold(self, reason=None):
        """تعليق التسجيل"""
        if self.status == 'active':
            self.status = 'on_hold'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] On Hold: {reason}"
            self.save()
            return True
        return False
    
    def withdraw(self, reason=None):
        """انسحاب الطالب من البرنامج"""
        if self.status in ['active', 'on_hold']:
            self.status = 'withdrawn'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Withdrawn: {reason}"
            self.save()
            return True
        return False
    
    def graduate(self):
        """تخريج الطالب"""
        if self.status == 'active':
            self.status = 'graduated'
            self.actual_graduation_date = timezone.now().date()
            self.save()
            return True
        return False
    
    def dismiss(self, reason=None):
        """فصل الطالب من البرنامج"""
        if self.status in ['active', 'on_hold']:
            self.status = 'dismissed'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Dismissed: {reason}"
            self.save()
            return True
        return False
    
    def change_study_plan(self, new_study_plan, reason=None):
        """تغيير الخطة الدراسية للطالب"""
        old_plan = self.study_plan
        self.study_plan = new_study_plan
        if reason:
            self.notes = f"{self.notes}\n[{timezone.now().date()}] Study Plan Changed from {old_plan} to {new_study_plan}: {reason}"
        self.save()
        return True
    
    def change_advisor(self, new_advisor, reason=None):
        """تغيير المرشد الأكاديمي للطالب"""
        old_advisor = self.advisor
        self.advisor = new_advisor
        if reason:
            self.notes = f"{self.notes}\n[{timezone.now().date()}] Advisor Changed from {old_advisor} to {new_advisor}: {reason}"
        self.save()
        return True


class SemesterRegistration(models.Model):
    """نموذج تسجيل الطالب في الفصل الدراسي"""
    
    REGISTRATION_STATUS = [
        ('draft', _('Draft')),
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('withdrawn', _('Withdrawn')),
    ]
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='semester_registrations',
        verbose_name=_("Student")
    )
    
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        related_name='semester_registrations',
        verbose_name=_("Academic Year")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='semester_registrations',
        verbose_name=_("Semester")
    )
    
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registration Date")
    )
    
    status = models.CharField(
        max_length=20,
        choices=REGISTRATION_STATUS,
        default='draft',
        verbose_name=_("Status")
    )
    
    approved_by = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_registrations',
        verbose_name=_("Approved By")
    )
    
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )
    
    total_credits = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Credits")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Semester Registration")
        verbose_name_plural = _("Semester Registrations")
        unique_together = [['student', 'academic_year', 'semester']]
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.academic_year.name} {self.semester.name}"
    
    def submit(self):
        """تقديم التسجيل للموافقة"""
        if self.status == 'draft':
            self.status = 'pending'
            self.save()
            return True
        return False
    
    def approve(self, approved_by):
        """الموافقة على التسجيل"""
        if self.status == 'pending':
            self.status = 'approved'
            self.approved_by = approved_by
            self.approval_date = timezone.now()
            self.save()
            return True
        return False
    
    def reject(self, reason=None):
        """رفض التسجيل"""
        if self.status == 'pending':
            self.status = 'rejected'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Rejected: {reason}"
            self.save()
            return True
        return False
    
    def activate(self):
        """تنشيط التسجيل (بداية الفصل الدراسي)"""
        if self.status == 'approved':
            self.status = 'active'
            self.save()
            return True
        return False
    
    def complete(self):
        """إكمال التسجيل (نهاية الفصل الدراسي)"""
        if self.status == 'active':
            self.status = 'completed'
            self.save()
            return True
        return False
    
    def withdraw(self, reason=None):
        """انسحاب الطالب من الفصل الدراسي"""
        if self.status in ['approved', 'active']:
            self.status = 'withdrawn'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Withdrawn: {reason}"
            self.save()
            return True
        return False
    
    def calculate_total_credits(self):
        """حساب إجمالي الساعات المعتمدة للتسجيل"""
        total = self.course_registrations.filter(
            status__in=['registered', 'completed']
        ).aggregate(
            total=Sum('course_section__course__credit_hours')
        )['total'] or 0
        
        self.total_credits = total
        self.save(update_fields=['total_credits'])
        return total
    
    def validate_registration(self):
        """التحقق من صحة التسجيل"""
        # 1. التحقق من عدد الساعات
        self.calculate_total_credits()
        program_settings = self.student.program.settings
        
        if self.semester.semester_type == 'summer':
            max_credits = program_settings.max_summer_credits
            if self.total_credits > max_credits:
                raise ValidationError(
                    _("Total credits ({}) exceed maximum allowed for summer semester ({})").format(
                        self.total_credits, max_credits
                    )
                )
        else:
            min_credits = program_settings.min_credits_per_semester
            max_credits = program_settings.max_credits_per_semester
            
            if self.total_credits < min_credits:
                raise ValidationError(
                    _("Total credits ({}) are below minimum required ({})").format(
                        self.total_credits, min_credits
                    )
                )
            
            if self.total_credits > max_credits:
                # يمكن استثناء الطلاب ذوي المعدل المرتفع
                if self.student.cgpa < 3.0:
                    raise ValidationError(
                        _("Total credits ({}) exceed maximum allowed ({})").format(
                            self.total_credits, max_credits
                        )
                    )
        
        # 2. التحقق من المتطلبات السابقة
        for registration in self.course_registrations.all():
            course = registration.course_section.course
            
            # التحقق من المتطلبات السابقة
            prerequisites = course.prerequisite_courses.all()
            for prereq in prerequisites:
                if not self.student.has_passed_course(prereq):
                    raise ValidationError(
                        _("Student has not passed prerequisite course: {}").format(
                            prereq.name
                        )
                    )
        
        return True


class CourseRegistration(models.Model):
    """نموذج تسجيل الطالب في مقرر"""
    
    REGISTRATION_STATUS = [
        ('registered', _('Registered')),
        ('dropped', _('Dropped')),
        ('withdrawn', _('Withdrawn')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('incomplete', _('Incomplete')),
    ]
    
    semester_registration = models.ForeignKey(
        'SemesterRegistration',
        on_delete=models.CASCADE,
        related_name='course_registrations',
        verbose_name=_("Semester Registration")
    )
    
    course_section = models.ForeignKey(
        'academic.CourseSection',
        on_delete=models.CASCADE,
        related_name='student_registrations',
        verbose_name=_("Course Section")
    )
    
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registration Date")
    )
    
    status = models.CharField(
        max_length=20,
        choices=REGISTRATION_STATUS,
        default='registered',
        verbose_name=_("Status")
    )
    
    grade = models.ForeignKey(
        'academic.StudentGrade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='course_registration',
        verbose_name=_("Grade")
    )
    
    is_repeat = models.BooleanField(
        default=False,
        verbose_name=_("Is Repeat")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Course Registration")
        verbose_name_plural = _("Course Registrations")
        unique_together = [['semester_registration', 'course_section']]
        
    def __str__(self):
        return f"{self.semester_registration.student.user.get_full_name()} - {self.course_section.course.name}"
    
    def drop(self, reason=None):
        """حذف المقرر (خلال فترة الحذف والإضافة)"""
        if self.status == 'registered' and self.semester_registration.semester.is_add_drop_period():
            self.status = 'dropped'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Dropped: {reason}"
            self.save()
            
            # تحديث إجمالي الساعات المعتمدة للتسجيل
            self.semester_registration.calculate_total_credits()
            return True
        return False
    
    def withdraw(self, reason=None):
        """الانسحاب من المقرر (بعد فترة الحذف والإضافة)"""
        if self.status == 'registered' and self.semester_registration.semester.is_withdrawal_allowed():
            self.status = 'withdrawn'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Withdrawn: {reason}"
            self.save()
            return True
        return False
    
    def complete(self, grade_value=None):
        """إكمال المقرر بنجاح"""
        if self.status == 'registered':
            self.status = 'completed'
            
            # إذا تم تحديد درجة، نقوم بإنشاء سجل درجة للطالب
            if grade_value is not None:
                from academic.models import StudentGrade, Grade
                
                # البحث عن درجة مناسبة
                grade = Grade.objects.get_grade_for_value(grade_value)
                
                # إنشاء سجل درجة للطالب
                student_grade = StudentGrade.objects.create(
                    student=self.semester_registration.student,
                    course=self.course_section.course,
                    grade=grade,
                    numeric_value=grade_value,
                    semester=self.semester_registration.semester
                )
                
                self.grade = student_grade
            
            self.save()
            return True
        return False
    
    def fail(self, grade_value=None):
        """رسوب الطالب في المقرر"""
        if self.status == 'registered':
            self.status = 'failed'
            
            # إذا تم تحديد درجة، نقوم بإنشاء سجل درجة للطالب
            if grade_value is not None:
                from academic.models import StudentGrade, Grade
                
                # البحث عن درجة مناسبة
                grade = Grade.objects.get_grade_for_value(grade_value)
                
                # إنشاء سجل درجة للطالب
                student_grade = StudentGrade.objects.create(
                    student=self.semester_registration.student,
                    course=self.course_section.course,
                    grade=grade,
                    numeric_value=grade_value,
                    semester=self.semester_registration.semester
                )
                
                self.grade = student_grade
            
            self.save()
            return True
        return False
    
    def mark_incomplete(self, reason=None):
        """تعليم المقرر كغير مكتمل"""
        if self.status == 'registered':
            self.status = 'incomplete'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Incomplete: {reason}"
            self.save()
            return True
        return False
