from django.db import models
from django.utils.translation import gettext_lazy as _

#  نموذج خيارات الدرجات الاكاديمية الثابتة 
class AcademicDegreeChoices(models.TextChoices):
    DIPLOMA = 'Diploma', _('diploma')
    BACHELOR = 'BSc', _('bachelor')
    MASTER = 'MSc', _('master')
    PHD = 'Phd', _('phd')

#نموذج البرامج الاكاديمية التابعة لقسم معين
class Program(models.Model):
    name = models.CharField(max_length=255,verbose_name=_("Program Name"))
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE, related_name='programs',verbose_name=_("Department"))
    degree_type = models.CharField(max_length=25,choices=AcademicDegreeChoices.choices,verbose_name=_("Program degree Type"))
    duration_years = models.PositiveSmallIntegerField(default=4,verbose_name=_("Program duration in years"))
    description = models.TextField(blank=True, null=True,verbose_name=_("Program Description"))
    study_system = models.CharField(max_length=255,verbose_name=_("Study System"))

    class Meta:
        verbose_name = _("Program")
        verbose_name_plural = _("Programs")
    def __str__(self):
        return f" {self.get_degree_type_display()} {self.name}"

#نموذج المستويات الدراسية التابعة لبرنامج معين
class ProgramLevel(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='levels')
    name = models.CharField(max_length=255,verbose_name="Level Name",null=True,blank=True)
    level_number = models.PositiveSmallIntegerField(verbose_name="Level Number",required=True)

    class Meta:
        unique_together = ('program', 'level_number')
        index_together = ('program', 'level_number')
        ordering = ['level_number','program']
        verbose_name = _("Program Level")
        verbose_name_plural = _("Program Levels")
    
    def get_level_display_name(self):
        level_names = {
            1: _("first level"),
            2: _("second level"),
            3: _("third level"),
            4: _("fourth level"),
            5: _("fifth level"),
            6: _("sixth level"),
            7: _("seventh level"),

        }
        return level_names.get(self.level_number, _("Level %(level)s") % {'level': self.level_number})

    def __str__(self):
        return _("%(program)s - %(level_name)s") % {
            'program': self.program.name,
            'level_name': self.get_level_display_name()
        }

