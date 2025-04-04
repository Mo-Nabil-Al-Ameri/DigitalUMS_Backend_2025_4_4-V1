"""
نماذج السنة الأكاديمية والفصول الدراسية
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class AcademicYear(models.Model):
    """نموذج السنة الأكاديمية"""
    
    name = models.CharField(
        max_length=50,
        verbose_name=_("Academic Year Name"),
        help_text=_("e.g. 2025-2026")
    )
    
    start_date = models.DateField(
        verbose_name=_("Start Date")
    )
    
    end_date = models.DateField(
        verbose_name=_("End Date")
    )
    
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Is Current Academic Year")
    )
    
    class Meta:
        verbose_name = _("Academic Year")
        verbose_name_plural = _("Academic Years")
        ordering = ['-start_date']
        
    def __str__(self):
        return self.name
    
    def clean(self):
        """التحقق من صحة البيانات"""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({
                'end_date': _("End date must be after start date")
            })
        
        if self.is_current:
            # التأكد من عدم وجود سنة أكاديمية أخرى حالية
            current_years = AcademicYear.objects.filter(is_current=True)
            if self.pk:
                current_years = current_years.exclude(pk=self.pk)
            if current_years.exists():
                raise ValidationError({
                    'is_current': _("Another academic year is already set as current")
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_current(cls):
        """الحصول على السنة الأكاديمية الحالية"""
        try:
            return cls.objects.get(is_current=True)
        except cls.DoesNotExist:
            # إذا لم يتم تعيين سنة أكاديمية حالية، نحاول العثور على السنة التي تتضمن التاريخ الحالي
            today = timezone.now().date()
            try:
                return cls.objects.get(start_date__lte=today, end_date__gte=today)
            except cls.DoesNotExist:
                return None


class Semester(models.Model):
    """نموذج الفصل الدراسي"""
    
    SEMESTER_TYPES = [
        ('fall', _('Fall')),
        ('spring', _('Spring')),
        ('summer', _('Summer')),
    ]
    
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='semesters',
        verbose_name=_("Academic Year")
    )
    
    name = models.CharField(
        max_length=50,
        verbose_name=_("Semester Name")
    )
    
    semester_type = models.CharField(
        max_length=10,
        choices=SEMESTER_TYPES,
        verbose_name=_("Semester Type")
    )
    
    start_date = models.DateField(
        verbose_name=_("Start Date")
    )
    
    end_date = models.DateField(
        verbose_name=_("End Date")
    )
    
    registration_start_date = models.DateField(
        verbose_name=_("Registration Start Date")
    )
    
    registration_end_date = models.DateField(
        verbose_name=_("Registration End Date")
    )
    
    add_drop_end_date = models.DateField(
        verbose_name=_("Add/Drop End Date")
    )
    
    withdrawal_deadline = models.DateField(
        verbose_name=_("Withdrawal Deadline")
    )
    
    final_exams_start_date = models.DateField(
        verbose_name=_("Final Exams Start Date")
    )
    
    final_exams_end_date = models.DateField(
        verbose_name=_("Final Exams End Date")
    )
    
    grades_due_date = models.DateField(
        verbose_name=_("Grades Due Date")
    )
    
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Is Current Semester")
    )
    
    class Meta:
        verbose_name = _("Semester")
        verbose_name_plural = _("Semesters")
        ordering = ['academic_year', 'start_date']
        unique_together = [['academic_year', 'semester_type']]
        
    def __str__(self):
        return f"{self.academic_year.name} - {self.get_semester_type_display()}"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({
                'end_date': _("End date must be after start date")
            })
        
        if self.registration_start_date and self.registration_end_date and self.registration_start_date >= self.registration_end_date:
            raise ValidationError({
                'registration_end_date': _("Registration end date must be after start date")
            })
        
        if self.final_exams_start_date and self.final_exams_end_date and self.final_exams_start_date >= self.final_exams_end_date:
            raise ValidationError({
                'final_exams_end_date': _("Final exams end date must be after start date")
            })
        
        if self.is_current:
            # التأكد من عدم وجود فصل دراسي آخر حالي
            current_semesters = Semester.objects.filter(is_current=True)
            if self.pk:
                current_semesters = current_semesters.exclude(pk=self.pk)
            if current_semesters.exists():
                raise ValidationError({
                    'is_current': _("Another semester is already set as current")
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_current(cls):
        """الحصول على الفصل الدراسي الحالي"""
        try:
            return cls.objects.get(is_current=True)
        except cls.DoesNotExist:
            # إذا لم يتم تعيين فصل دراسي حالي، نحاول العثور على الفصل الذي يتضمن التاريخ الحالي
            today = timezone.now().date()
            try:
                return cls.objects.get(start_date__lte=today, end_date__gte=today)
            except cls.DoesNotExist:
                return None
    
    def is_registration_open(self):
        """التحقق مما إذا كانت فترة التسجيل مفتوحة"""
        today = timezone.now().date()
        return self.registration_start_date <= today <= self.registration_end_date
    
    def is_add_drop_period(self):
        """التحقق مما إذا كانت فترة الإضافة والحذف مفتوحة"""
        today = timezone.now().date()
        return self.registration_end_date < today <= self.add_drop_end_date
    
    def is_withdrawal_allowed(self):
        """التحقق مما إذا كان الانسحاب من المقررات مسموحاً"""
        today = timezone.now().date()
        return today <= self.withdrawal_deadline
    
    def is_final_exams_period(self):
        """التحقق مما إذا كانت فترة الاختبارات النهائية"""
        today = timezone.now().date()
        return self.final_exams_start_date <= today <= self.final_exams_end_date
