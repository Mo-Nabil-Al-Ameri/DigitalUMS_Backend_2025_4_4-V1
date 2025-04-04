"""
نماذج إدارة المقررات الدراسية وجدولتها
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CourseSection(models.Model):
    """نموذج شعبة المقرر الدراسي"""
    
    SECTION_STATUS = [
        ('planned', _('Planned')),
        ('open', _('Open for Registration')),
        ('closed', _('Closed for Registration')),
        ('canceled', _('Canceled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
    ]
    
    course = models.ForeignKey(
        'departments.Course',
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_("Course")
    )
    
    section_number = models.CharField(
        max_length=10,
        verbose_name=_("Section Number")
    )
    
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        related_name='course_sections',
        verbose_name=_("Academic Year")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='course_sections',
        verbose_name=_("Semester")
    )
    
    capacity = models.PositiveIntegerField(
        verbose_name=_("Capacity")
    )
    
    enrolled_students = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Enrolled Students")
    )
    
    status = models.CharField(
        max_length=20,
        choices=SECTION_STATUS,
        default='planned',
        verbose_name=_("Status")
    )
    
    location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Location")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    syllabus = models.FileField(
        upload_to='syllabi/',
        null=True,
        blank=True,
        verbose_name=_("Syllabus")
    )
    
    class Meta:
        verbose_name = _("Course Section")
        verbose_name_plural = _("Course Sections")
        unique_together = [['course', 'section_number', 'semester']]
        ordering = ['course', 'section_number']
        
    def __str__(self):
        return f"{self.course.code}-{self.section_number} ({self.semester})"
    
    def open_for_registration(self):
        """فتح الشعبة للتسجيل"""
        if self.status == 'planned':
            self.status = 'open'
            self.save()
            return True
        return False
    
    def close_registration(self):
        """إغلاق التسجيل في الشعبة"""
        if self.status == 'open':
            self.status = 'closed'
            self.save()
            return True
        return False
    
    def cancel(self, reason=None):
        """إلغاء الشعبة"""
        if self.status in ['planned', 'open']:
            self.status = 'canceled'
            if reason:
                self.notes = f"{self.notes}\n[{timezone.now().date()}] Canceled: {reason}"
            self.save()
            return True
        return False
    
    def start(self):
        """بدء تدريس الشعبة"""
        if self.status in ['open', 'closed']:
            self.status = 'in_progress'
            self.save()
            return True
        return False
    
    def complete(self):
        """إكمال تدريس الشعبة"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.save()
            return True
        return False
    
    def update_enrollment_count(self):
        """تحديث عدد الطلاب المسجلين"""
        from academic.models import CourseRegistration
        
        count = CourseRegistration.objects.filter(
            course_section=self,
            status='registered'
        ).count()
        
        self.enrolled_students = count
        self.save(update_fields=['enrolled_students'])
        return count
    
    def has_available_seats(self):
        """التحقق من توفر مقاعد شاغرة"""
        return self.enrolled_students < self.capacity
    
    def get_instructors(self):
        """الحصول على قائمة المدرسين"""
        return self.instructors.all()
    
    def get_schedule(self):
        """الحصول على جدول المحاضرات"""
        return self.schedule.all()


class CourseSectionSchedule(models.Model):
    """نموذج جدول محاضرات شعبة المقرر"""
    
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    
    SCHEDULE_TYPES = [
        ('lecture', _('Lecture')),
        ('lab', _('Laboratory')),
        ('tutorial', _('Tutorial')),
        ('discussion', _('Discussion')),
        ('other', _('Other')),
    ]
    
    course_section = models.ForeignKey(
        'CourseSection',
        on_delete=models.CASCADE,
        related_name='schedule',
        verbose_name=_("Course Section")
    )
    
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAYS_OF_WEEK,
        verbose_name=_("Day of Week")
    )
    
    start_time = models.TimeField(
        verbose_name=_("Start Time")
    )
    
    end_time = models.TimeField(
        verbose_name=_("End Time")
    )
    
    location = models.CharField(
        max_length=100,
        verbose_name=_("Location")
    )
    
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPES,
        default='lecture',
        verbose_name=_("Schedule Type")
    )
    
    instructor = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_schedules',
        verbose_name=_("Instructor")
    )
    
    class Meta:
        verbose_name = _("Course Section Schedule")
        verbose_name_plural = _("Course Section Schedules")
        ordering = ['course_section', 'day_of_week', 'start_time']
        
    def __str__(self):
        return f"{self.course_section} - {self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': _("End time must be after start time")
            })
        
        # التحقق من عدم وجود تعارض في جدول المدرس
        if self.instructor:
            conflicts = CourseSectionSchedule.objects.filter(
                instructor=self.instructor,
                day_of_week=self.day_of_week
            ).exclude(pk=self.pk)
            
            for schedule in conflicts:
                if (
                    (self.start_time <= schedule.start_time < self.end_time) or
                    (self.start_time < schedule.end_time <= self.end_time) or
                    (schedule.start_time <= self.start_time < schedule.end_time) or
                    (schedule.start_time < self.end_time <= schedule.end_time)
                ):
                    raise ValidationError({
                        'instructor': _("Instructor has a schedule conflict with {conflict}").format(
                            conflict=schedule
                        )
                    })
        
        # التحقق من عدم وجود تعارض في المكان
        conflicts = CourseSectionSchedule.objects.filter(
            location=self.location,
            day_of_week=self.day_of_week
        ).exclude(pk=self.pk)
        
        for schedule in conflicts:
            if (
                (self.start_time <= schedule.start_time < self.end_time) or
                (self.start_time < schedule.end_time <= self.end_time) or
                (schedule.start_time <= self.start_time < schedule.end_time) or
                (schedule.start_time < self.end_time <= schedule.end_time)
            ):
                raise ValidationError({
                    'location': _("Location is already booked during this time for {conflict}").format(
                        conflict=schedule
                    )
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def get_duration_minutes(self):
        """حساب مدة المحاضرة بالدقائق"""
        if not self.start_time or not self.end_time:
            return 0
            
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes


class CourseInstructor(models.Model):
    """نموذج مدرس المقرر"""
    
    INSTRUCTOR_ROLES = [
        ('primary', _('Primary Instructor')),
        ('secondary', _('Secondary Instructor')),
        ('assistant', _('Teaching Assistant')),
        ('lab', _('Lab Instructor')),
        ('guest', _('Guest Lecturer')),
    ]
    
    course_section = models.ForeignKey(
        'CourseSection',
        on_delete=models.CASCADE,
        related_name='instructors',
        verbose_name=_("Course Section")
    )
    
    instructor = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        verbose_name=_("Instructor")
    )
    
    role = models.CharField(
        max_length=20,
        choices=INSTRUCTOR_ROLES,
        default='primary',
        verbose_name=_("Role")
    )
    
    assignment_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Assignment Date")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Course Instructor")
        verbose_name_plural = _("Course Instructors")
        unique_together = [['course_section', 'instructor']]
        
    def __str__(self):
        return f"{self.instructor.user.get_full_name()} - {self.course_section} ({self.get_role_display()})"
