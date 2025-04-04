from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Max
from .utils import generate_college_number, format_college_number, validate_college_number
from apps.core.numbering import BaseNumberingSystem, CollegeNumbering

class University(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("University Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("University Description"))
    location = models.CharField(max_length=255, verbose_name=_("University Location"))

    class Meta:
        verbose_name = _("University")
        verbose_name_plural = _("Universities")

    def __str__(self):
        return self.name

class UniversityDetail(models.Model):
    title = models.CharField(max_length=150,verbose_name=_("Detail Title"))
    subtitle = models.TextField(verbose_name=_("Detail subtitle"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='details',verbose_name=_("University"))

    def __str__(self):
        return f"{self.title}"

#نموذج الكليات الدراسية الخاصة بالجامعة
class College(models.Model):
    code = models.IntegerField(
        unique=True,
        verbose_name=_("College Code"),
        editable=False,  # لمنع التعديل اليدوي
        help_text=_("Unique numeric identifier for the college")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("College Name"),
        help_text=_("Full name of the college")
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("College Description"),
        help_text=_("Detailed description of the college")
    )
    
    class Meta:
        verbose_name = _("College")
        verbose_name_plural = _("Colleges")
        ordering = ['code']
        indexes = [
            models.Index(fields=['code', 'name'], name='college_code_name_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            # توليد رقم الكلية إذا كان جديداً
            self.code = generate_college_number(self.__class__)
        super().save(*args, **kwargs)

    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من الرقم
        if self.code:
            validate_college_number(self.code)

        if not self.name or not self.name.strip():
            raise ValidationError({
                'name': _('College name is required')
            })

    def __str__(self):
        return f"{self.format_code()} - {self.name}"

    def format_code(self) -> str:
        """تنسيق رقم الكلية"""
        if not self.code:
            return ''
        return format_college_number(self.code)

#نموذج تفاصيل الكلية 
class CollegeDetail(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='details', verbose_name=_("College"))
    title = models.CharField(max_length=150, verbose_name=_("Detail Title"))
    subtitle = models.TextField(verbose_name=_("Detail subtitle"))

    class Meta:
        verbose_name = _("College Detail")
        verbose_name_plural = _("College Details")

    def __str__(self):
        return f"{self.title}"
