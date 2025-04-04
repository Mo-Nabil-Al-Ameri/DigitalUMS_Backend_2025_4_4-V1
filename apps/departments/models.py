#this app is for departments and their programs
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Count, Sum
import re

from apps.core.numbering import BaseNumberingSystem, DepartmentNumbering
from .utils import (
    generate_department_number,
    format_department_number,
    validate_department_number,
    get_unique_department_code,
    department_image_path
)

# نموذج اقسام الكليات 
class Department(models.Model):
    """نموذج القسم الأكاديمي أو الإداري"""
    
    DEPARTMENT_TYPES = [
        ('academic', _('Academic Department')),
        ('administrative', _('Administrative Department')),
    ]

    dep_no = models.IntegerField(
        primary_key=True,
        verbose_name=_("Department Number"),
        editable=False
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Department Code"),
        help_text=_("Department code (automatically generated from name)")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Department Name"),
        help_text=_("Full name of the department")
    )
    department_type = models.CharField(
        max_length=20,
        choices=DEPARTMENT_TYPES,
        default='academic',
        verbose_name=_("Department Type"),
        help_text=_("Type of department (academic or administrative)")
    )
    college = models.ForeignKey(
        'university.College',
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_("College"),
        help_text=_("The college this department belongs to (optional for administrative departments)"),
        null=True,
        blank=True
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Department Description")
    )
    image = models.ImageField(
        upload_to=department_image_path,
        null=True,
        blank=True,
        verbose_name=_("Department Image"),
        help_text=_("Department logo or representative image"),
        max_length=255
    )
    department_vision = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Department Vision")
    )
    department_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Department Message")
    )

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        indexes = [
            models.Index(fields=['code', 'name'], name='code_name_index'),
            models.Index(fields=['college'], name='college_departments_index'),
            models.Index(fields=['department_type'], name='department_type_index'),
        ]
        ordering = ['dep_no']

    def save(self, *args, **kwargs):
        if not self.dep_no:
            self.dep_no = generate_department_number(
                model_class=self.__class__,
                college_id=self.college_id if self.college else None,
                department_type=self.department_type
            )
        
        # توليد الاختصار من اسم القسم
        if self.name and not self.code:
            self.code = get_unique_department_code(
                model_class=self.__class__,
                name=self.name,
                max_length=10
            )
        
        super().save(*args, **kwargs)

    def clean(self):
        """التحقق من صحة البيانات"""
        super().clean()
        
        # التحقق من نوع القسم والكلية
        if self.department_type == 'academic' and not self.college:
            raise ValidationError({
                'college': _('Academic departments must be associated with a college')
            })
            
        # التحقق من الرقم
        if self.dep_no:
            validate_department_number(self.dep_no)
        
        # التحقق من الاختصار
        if self.code:
            if len(self.code) > 10:
                raise ValidationError({
                    'code': _('Department code cannot be longer than 10 characters')
                })

    def format_number(self) -> str:
        """تنسيق رقم القسم"""
        if not self.dep_no:
            return ''
            
        return format_department_number(
            number=self.dep_no,
            college_code=self.college.code if self.college else None,
            department_type=self.department_type
        )

    def __str__(self):
        return f"{self.format_number()} - {self.name}"

class AcademicProgram(models.Model):
    """نموذج البرنامج الأكاديمي وفقاً لمعايير بولونيا"""
    
    DEGREE_LEVELS = [
        ('bachelor', _('Bachelor')),
        ('master', _('Master')),
        ('phd', _('PhD')),
    ]
    
    PROGRAM_TYPES = [
        ('full_time', _('Full Time')),
        ('part_time', _('Part Time')),
        ('distance', _('Distance Learning')),
    ]

    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Program Code")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Program Name")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name=_("Department"),
        limit_choices_to={'department_type': 'academic'}
    )
    degree_level = models.CharField(
        max_length=20,
        choices=DEGREE_LEVELS,
        verbose_name=_("Degree Level")
    )
    program_type = models.CharField(
        max_length=20,
        choices=PROGRAM_TYPES,
        default='full_time',
        verbose_name=_("Program Type")
    )
    total_credits = models.PositiveIntegerField(
        verbose_name=_("Total Credits"),
        help_text=_("Total ECTS credits required for graduation")
    )
    duration_years = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name=_("Duration (Years)"),
        help_text=_("Standard duration in years")
    )
    language = models.CharField(
        max_length=50,
        verbose_name=_("Teaching Language")
    )
    description = models.TextField(
        verbose_name=_("Program Description")
    )
    learning_outcomes = models.TextField(
        verbose_name=_("Learning Outcomes"),
        help_text=_("Program learning outcomes according to Bologna standards")
    )
    admission_requirements = models.TextField(
        verbose_name=_("Admission Requirements")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Status")
    )

    class Meta:
        verbose_name = _("Academic Program")
        verbose_name_plural = _("Academic Programs")
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='program_code_idx'),
            models.Index(fields=['degree_level'], name='degree_level_idx'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

class Course(models.Model):
    """نموذج المقرر الدراسي وفقاً لمعايير بولونيا"""
    
    COURSE_TYPES = [
        ('mandatory', _('Mandatory')),
        ('elective', _('Elective')),
        ('optional', _('Optional')),
    ]
    
    COURSE_LEVELS = [
        ('introductory', _('Introductory')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    ]
    
    GRADING_METHODS = [
        ('letter', _('Letter Grade')),
        ('pass_fail', _('Pass/Fail')),
        ('percentage', _('Percentage')),
    ]

    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Course Code"),
        help_text=_("Format: DEPT-NUM (e.g. CS-101)")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Course Name")
    )
    programs = models.ManyToManyField(
        AcademicProgram,
        through='ProgramCourse',
        related_name='courses',
        verbose_name=_("Programs")
    )
    credits = models.PositiveIntegerField(
        verbose_name=_("ECTS Credits"),
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text=_("European Credit Transfer System (ECTS) credits")
    )
    hours_lecture = models.PositiveIntegerField(
        verbose_name=_("Lecture Hours"),
        validators=[MinValueValidator(0)]
    )
    hours_lab = models.PositiveIntegerField(
        verbose_name=_("Lab Hours"),
        default=0,
        validators=[MinValueValidator(0)]
    )
    hours_tutorial = models.PositiveIntegerField(
        verbose_name=_("Tutorial Hours"),
        default=0,
        validators=[MinValueValidator(0)]
    )
    course_type = models.CharField(
        max_length=20,
        choices=COURSE_TYPES,
        verbose_name=_("Course Type")
    )
    course_level = models.CharField(
        max_length=20,
        choices=COURSE_LEVELS,
        verbose_name=_("Course Level")
    )
    description = models.TextField(
        verbose_name=_("Course Description")
    )
    learning_outcomes = models.TextField(
        verbose_name=_("Learning Outcomes"),
        help_text=_("List the learning outcomes separated by new lines")
    )
    prerequisites = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='prerequisite_for',
        verbose_name=_("Prerequisites")
    )
    corequisites = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='corequisite_for',
        verbose_name=_("Corequisites"),
        help_text=_("Courses that must be taken simultaneously with this course")
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_("Department")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Status")
    )
    grading_method = models.CharField(
        max_length=20,
        choices=GRADING_METHODS,
        default='letter',
        verbose_name=_("Grading Method")
    )
    min_passing_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60.00,
        verbose_name=_("Minimum Passing Grade"),
        help_text=_("Minimum grade required to pass the course (percentage)")
    )
    syllabus_file = models.FileField(
        upload_to='syllabi/',
        null=True,
        blank=True,
        verbose_name=_("Syllabus File")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ['code']
        indexes = [
            models.Index(fields=['code'], name='course_code_idx'),
            models.Index(fields=['course_type'], name='course_type_idx'),
            models.Index(fields=['course_level'], name='course_level_idx'),
            models.Index(fields=['department', 'is_active'], name='dept_active_idx'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """التحقق من صحة بيانات المقرر"""
        super().clean()
        
        # التحقق من تنسيق رمز المقرر (مثال: CS-101)
        if self.code:
            code_pattern = r'^[A-Z]{2,4}-\d{3,4}$'
            if not re.match(code_pattern, self.code):
                raise ValidationError({
                    'code': _('Course code must be in format DEPT-NUM (e.g. CS-101)')
                })
        
        # التحقق من إجمالي ساعات المقرر
        total_hours = self.hours_lecture + self.hours_lab + self.hours_tutorial
        if total_hours == 0:
            raise ValidationError({
                'hours_lecture': _('Total course hours (lecture, lab, tutorial) must be greater than zero')
            })
        
        # التحقق من تناسب الساعات مع عدد الساعات المعتمدة
        expected_min_hours = self.credits * 1  # على الأقل ساعة واحدة لكل ساعة معتمدة
        if total_hours < expected_min_hours:
            raise ValidationError({
                'credits': _('Total hours are insufficient for the specified credits')
            })
    
    def save(self, *args, **kwargs):
        """حفظ المقرر مع التحقق من صحة البيانات"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_total_hours(self):
        """حساب إجمالي ساعات المقرر"""
        return self.hours_lecture + self.hours_lab + self.hours_tutorial
    
    def get_learning_outcomes_list(self):
        """الحصول على قائمة بنتائج التعلم"""
        if not self.learning_outcomes:
            return []
        return [outcome.strip() for outcome in self.learning_outcomes.split('\n') if outcome.strip()]
    
    def get_all_prerequisites(self, include_indirect=False):
        """الحصول على جميع المتطلبات السابقة (المباشرة وغير المباشرة)"""
        direct_prereqs = self.prerequisites.filter(is_active=True)
        
        if not include_indirect:
            return direct_prereqs
        
        # الحصول على المتطلبات غير المباشرة (متطلبات المتطلبات)
        all_prereqs = set(direct_prereqs)
        for prereq in direct_prereqs:
            all_prereqs.update(prereq.get_all_prerequisites(include_indirect=True))
        
        return all_prereqs
    
    def check_circular_prerequisites(self):
        """التحقق من عدم وجود متطلبات دائرية"""
        visited = set()
        path = [self]
        
        def dfs(course):
            visited.add(course.id)
            for prereq in course.prerequisites.all():
                if prereq.id == self.id:  # وجدنا دورة
                    return True
                if prereq.id not in visited:
                    path.append(prereq)
                    if dfs(prereq):
                        return True
                    path.pop()
            return False
        
        return dfs(self)
    
    def is_available_in_semester(self, semester):
        """التحقق مما إذا كان المقرر متاحًا في فصل دراسي معين"""
        from apps.academic.models import CourseSection
        return CourseSection.objects.filter(
            course=self,
            semester=semester,
            status__in=['open', 'closed', 'in_progress']
        ).exists()

class ProgramCourse(models.Model):
    """نموذج العلاقة بين البرنامج والمقرر"""
    
    COURSE_STATUS = [
        ('active', _('Active')),
        ('archived', _('Archived')),
        ('pending_approval', _('Pending Approval')),
    ]
    
    program = models.ForeignKey(
        AcademicProgram,
        on_delete=models.CASCADE,
        related_name='program_courses',
        verbose_name=_("Program")
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='program_courses',
        verbose_name=_("Course")
    )
    
    semester = models.PositiveIntegerField(
        verbose_name=_("Semester"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("The semester number in which this course is offered")
    )
    
    is_required = models.BooleanField(
        default=True,
        verbose_name=_("Is Required"),
        help_text=_("Whether this course is required or elective in the program")
    )
    
    status = models.CharField(
        max_length=20,
        choices=COURSE_STATUS,
        default='active',
        verbose_name=_("Status")
    )
    
    min_grade_required = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60.00,
        verbose_name=_("Minimum Required Grade"),
        help_text=_("Minimum grade required to pass this course in this program")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    class Meta:
        verbose_name = _("Program Course")
        verbose_name_plural = _("Program Courses")
        unique_together = [['program', 'course']]
        ordering = ['semester', 'course__code']
        indexes = [
            models.Index(fields=['semester'], name='semester_idx'),
            models.Index(fields=['program', 'is_required'], name='program_required_idx'),
            models.Index(fields=['status'], name='program_course_status_idx'),
        ]
        
    def __str__(self):
        return f"{self.program.name} - {self.course.name} (Semester {self.semester})"
    
    def clean(self):
        """التحقق من صحة بيانات العلاقة بين البرنامج والمقرر"""
        super().clean()
        
        # التحقق من أن المقرر ينتمي إلى نفس القسم كالبرنامج أو أن المقرر متطلب جامعة عام
        if self.course.department.id != self.program.department.id:
            # التحقق مما إذا كان المقرر متطلب جامعة عام
            if not self.course.course_type == 'mandatory' and not self.is_required == False:
                raise ValidationError({
                    'course': _('Course must belong to the same department as the program or be a general university requirement')
                })
        
        # التحقق من أن الفصل الدراسي ضمن نطاق البرنامج
        program_settings = ProgramSettings.objects.filter(program=self.program).first()
        if program_settings:
            total_semesters = program_settings.calculate_total_semesters()
            if self.semester > total_semesters:
                raise ValidationError({
                    'semester': _('Semester number exceeds the total number of semesters in the program')
                })
    
    def save(self, *args, **kwargs):
        """حفظ العلاقة مع التحقق من صحة البيانات"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_prerequisite_courses(self):
        """الحصول على المقررات المتطلبة السابقة لهذا المقرر في البرنامج"""
        prereq_courses = self.course.prerequisites.all()
        return ProgramCourse.objects.filter(
            program=self.program,
            course__in=prereq_courses,
            status='active'
        )
    
    def check_prerequisites_in_earlier_semesters(self):
        """التحقق من أن جميع المتطلبات السابقة في فصول دراسية سابقة"""
        prereq_program_courses = self.get_prerequisite_courses()
        for prereq in prereq_program_courses:
            if prereq.semester >= self.semester:
                return False, prereq.course.code
        return True, None

class StudyPlan(models.Model):
    """نموذج الخطة الدراسية"""
    
    PLAN_STATUS = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('archived', _('Archived')),
    ]

    program = models.ForeignKey(
        AcademicProgram,
        on_delete=models.CASCADE,
        related_name='study_plans',
        verbose_name=_("Academic Program")
    )
    version = models.CharField(
        max_length=10,
        verbose_name=_("Plan Version"),
        help_text=_("e.g., 2025-1")
    )
    effective_from = models.DateField(
        verbose_name=_("Effective From Date")
    )
    effective_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Effective To Date")
    )
    total_credit_hours = models.PositiveIntegerField(
        verbose_name=_("Total Credit Hours")
    )
    status = models.CharField(
        max_length=20,
        choices=PLAN_STATUS,
        default='draft',
        verbose_name=_("Plan Status")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Plan Description")
    )
    approved_by = models.CharField(
        max_length=255,
        verbose_name=_("Approved By")
    )
    approval_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Approval Date")
    )

    class Meta:
        verbose_name = _("Study Plan")
        verbose_name_plural = _("Study Plans")
        unique_together = [['program', 'version']]
        ordering = ['-effective_from', 'version']
        indexes = [
            models.Index(fields=['status'], name='plan_status_idx'),
            models.Index(fields=['effective_from'], name='plan_effective_from_idx'),
        ]

    def __str__(self):
        return f"{self.program.name} - {self.version}"

    def clean(self):
        if self.effective_to and self.effective_from > self.effective_to:
            raise ValidationError({
                'effective_to': _("Effective end date must be after start date")
            })

class CourseGroup(models.Model):
    """نموذج مجموعة المقررات في الخطة الدراسية"""
    
    GROUP_TYPES = [
        ('university', _('University Requirements')),
        ('college', _('College Requirements')),
        ('program', _('Program Requirements')),
        ('specialization', _('Specialization Requirements')),
        ('elective', _('Elective Courses')),
    ]

    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='course_groups',
        verbose_name=_("Study Plan")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Group Name")
    )
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPES,
        verbose_name=_("Group Type")
    )
    required_credits = models.PositiveIntegerField(
        verbose_name=_("Required Credits")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Group Description")
    )
    order = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Display Order")
    )

    class Meta:
        verbose_name = _("Course Group")
        verbose_name_plural = _("Course Groups")
        ordering = ['study_plan', 'order', 'name']
        indexes = [
            models.Index(fields=['group_type'], name='group_type_idx'),
        ]

    def __str__(self):
        return f"{self.study_plan.program.name} - {self.name}"

class SemesterPlan(models.Model):
    """نموذج الخطة الفصلية"""
    
    SEMESTER_TYPES = [
        ('fall', _('Fall')),
        ('spring', _('Spring')),
        ('summer', _('Summer')),
    ]
    
    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='semester_plans',
        verbose_name=_("Study Plan")
    )
    
    year = models.PositiveSmallIntegerField(
        verbose_name=_("Year"),
        help_text=_("Academic year number in the program (1, 2, 3, etc.)")
    )
    
    semester_type = models.CharField(
        max_length=10,
        choices=SEMESTER_TYPES,
        verbose_name=_("Semester Type")
    )
    
    academic_level = models.ForeignKey(
        'AcademicLevel',
        on_delete=models.CASCADE,
        related_name='semester_plans',
        verbose_name=_("Academic Level"),
        help_text=_("The academic level this semester belongs to")
    )
    
    recommended_credits = models.PositiveIntegerField(
        default=15,
        verbose_name=_("Recommended Credits"),
        help_text=_("Recommended number of credits for this semester")
    )
    
    min_credits = models.PositiveIntegerField(
        default=12,
        verbose_name=_("Minimum Credits"),
        help_text=_("Minimum number of credits required for this semester")
    )
    
    max_credits = models.PositiveIntegerField(
        default=18,
        verbose_name=_("Maximum Credits"),
        help_text=_("Maximum number of credits allowed for this semester")
    )
    
    is_summer = models.BooleanField(
        default=False,
        verbose_name=_("Is Summer Semester"),
        help_text=_("Whether this is a summer semester with different credit limits")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    class Meta:
        verbose_name = _("Semester Plan")
        verbose_name_plural = _("Semester Plans")
        unique_together = [['study_plan', 'year', 'semester_type']]
        ordering = ['study_plan', 'year', 'semester_type']
        indexes = [
            models.Index(fields=['year', 'semester_type'], name='semester_year_type_idx'),
            models.Index(fields=['academic_level'], name='semester_level_idx'),
            models.Index(fields=['is_summer'], name='is_summer_idx'),
        ]
    
    def __str__(self):
        return f"{self.study_plan.name} - Year {self.year} {self.get_semester_type_display()}"
    
    def clean(self):
        """التحقق من صحة بيانات الخطة الفصلية"""
        super().clean()
        
        # التحقق من أن المستوى الأكاديمي ينتمي إلى نفس البرنامج
        if self.academic_level.program != self.study_plan.program:
            raise ValidationError({
                'academic_level': _("Academic level must belong to the same program as the study plan")
            })
        
        # التحقق من حدود الساعات المعتمدة
        if self.min_credits > self.max_credits:
            raise ValidationError({
                'min_credits': _("Minimum credits cannot be greater than maximum credits")
            })
        
        if self.recommended_credits < self.min_credits or self.recommended_credits > self.max_credits:
            raise ValidationError({
                'recommended_credits': _("Recommended credits must be between minimum and maximum credits")
            })
    
    def save(self, *args, **kwargs):
        """حفظ الخطة الفصلية مع التحقق من صحة البيانات"""
        # تعيين الفصل الصيفي تلقائياً
        if self.semester_type == 'summer':
            self.is_summer = True
            
        self.clean()
        super().save(*args, **kwargs)
    
    def get_total_credits(self):
        """حساب إجمالي الساعات المعتمدة للمقررات في هذا الفصل"""
        return self.semester_courses.aggregate(Sum('course__credits'))['course__credits__sum'] or 0
    
    def get_required_credits(self):
        """حساب الساعات المعتمدة للمقررات الإلزامية في هذا الفصل"""
        return self.semester_courses.filter(is_required=True).aggregate(Sum('course__credits'))['course__credits__sum'] or 0
    
    def get_elective_credits(self):
        """حساب الساعات المعتمدة للمقررات الاختيارية في هذا الفصل"""
        return self.semester_courses.filter(is_required=False).aggregate(Sum('course__credits'))['course__credits__sum'] or 0
    
    def map_to_academic_semester(self, academic_year):
        """ربط الخطة الفصلية بفصل دراسي فعلي في سنة أكاديمية محددة"""
        from apps.academic.models.academic_year import Semester
        
        try:
            # البحث عن الفصل الدراسي المناسب في السنة الأكاديمية المحددة
            return Semester.objects.get(
                academic_year=academic_year,
                semester_type=self.semester_type
            )
        except Semester.DoesNotExist:
            return None


class SemesterCourse(models.Model):
    """نموذج المقررات في الفصل الدراسي"""
    
    semester_plan = models.ForeignKey(
        SemesterPlan,
        on_delete=models.CASCADE,
        related_name='semester_courses',
        verbose_name=_("Semester Plan")
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='semester_courses',
        verbose_name=_("Course")
    )
    
    is_required = models.BooleanField(
        default=True,
        verbose_name=_("Is Required"),
        help_text=_("Whether this course is required in this semester")
    )
    
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='semester_courses',
        verbose_name=_("Course Group"),
        help_text=_("The course group this course belongs to in the study plan")
    )
    
    order = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Order"),
        help_text=_("Order of the course in the semester")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    class Meta:
        verbose_name = _("Semester Course")
        verbose_name_plural = _("Semester Courses")
        unique_together = [['semester_plan', 'course']]
        ordering = ['semester_plan', 'order', 'course__code']
        indexes = [
            models.Index(fields=['is_required'], name='course_required_idx'),
            models.Index(fields=['order'], name='course_order_idx'),
        ]
    
    def __str__(self):
        return f"{self.semester_plan} - {self.course.code}"
    
    def clean(self):
        """التحقق من صحة بيانات المقرر في الفصل"""
        super().clean()
        
        # التحقق من أن مجموعة المقررات تنتمي إلى نفس الخطة الدراسية
        if self.course_group and self.course_group.study_plan != self.semester_plan.study_plan:
            raise ValidationError({
                'course_group': _("Course group must belong to the same study plan")
            })
        
        # التحقق من المتطلبات السابقة للمقرر
        prerequisites = self.course.prerequisites.all()
        if prerequisites.exists():
            # التحقق من أن جميع المتطلبات السابقة موجودة في فصول سابقة
            current_semester_order = self.semester_plan.year * 10 + (
                1 if self.semester_plan.semester_type == 'fall' else 
                2 if self.semester_plan.semester_type == 'spring' else 3
            )
            
            for prereq in prerequisites:
                # البحث عن المقرر المتطلب في الخطة الدراسية
                prereq_courses = SemesterCourse.objects.filter(
                    semester_plan__study_plan=self.semester_plan.study_plan,
                    course=prereq
                )
                
                if not prereq_courses.exists():
                    continue  # قد يكون المتطلب غير موجود في الخطة الدراسية (مثل متطلبات القبول)
                
                for prereq_course in prereq_courses:
                    prereq_semester_order = prereq_course.semester_plan.year * 10 + (
                        1 if prereq_course.semester_plan.semester_type == 'fall' else 
                        2 if prereq_course.semester_plan.semester_type == 'spring' else 3
                    )
                    
                    if prereq_semester_order >= current_semester_order:
                        raise ValidationError({
                            'course': _("Prerequisite %(prereq)s must be in an earlier semester") % {
                                'prereq': prereq.code
                            }
                        })
    
    def save(self, *args, **kwargs):
        """حفظ المقرر في الفصل مع التحقق من صحة البيانات"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_actual_semester(self, academic_year):
        """الحصول على الفصل الدراسي الفعلي المقابل لهذا المقرر في السنة الأكاديمية المحددة"""
        return self.semester_plan.map_to_academic_semester(academic_year)


class ProgramSettings(models.Model):
    """نموذج إعدادات البرنامج"""
    
    GRADING_SYSTEMS = [
        ('letter', _('Letter Grades (A, B, C, D, F)')),
        ('percentage', _('Percentage (0-100%)')),
        ('gpa', _('GPA (0.0-4.0)')),
    ]
    
    SEMESTER_TYPES = [
        ('semester', _('Semester System')),
        ('quarter', _('Quarter System')),
        ('trimester', _('Trimester System')),
    ]
    
    program = models.OneToOneField(
        AcademicProgram,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name=_("Academic Program")
    )
    
    # مدة البرنامج
    standard_duration_years = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=4.0,
        verbose_name=_("Standard Duration (Years)"),
        help_text=_("Standard duration to complete the program"),
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)]
    )
    max_duration_years = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=6.0,
        verbose_name=_("Maximum Duration (Years)"),
        help_text=_("Maximum allowed duration to complete the program"),
        validators=[MinValueValidator(1.0), MaxValueValidator(12.0)]
    )
    min_credits_per_semester = models.PositiveIntegerField(
        default=12,
        verbose_name=_("Minimum Credits per Semester"),
        help_text=_("Minimum allowed credits per semester"),
        validators=[MinValueValidator(3), MaxValueValidator(30)]
    )
    max_credits_per_semester = models.PositiveIntegerField(
        default=18,
        verbose_name=_("Maximum Credits per Semester"),
        help_text=_("Maximum allowed credits per semester"),
        validators=[MinValueValidator(6), MaxValueValidator(30)]
    )
    summer_semester_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enable Summer Semester"),
        help_text=_("Whether summer semesters are available in this program")
    )
    max_summer_credits = models.PositiveIntegerField(
        default=9,
        verbose_name=_("Maximum Summer Credits"),
        help_text=_("Maximum allowed credits in summer semester"),
        validators=[MinValueValidator(3), MaxValueValidator(15)]
    )
    
    # متطلبات التخرج
    min_cgpa_required = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=2.00,
        verbose_name=_("Minimum Required CGPA"),
        help_text=_("Minimum CGPA required for graduation"),
        validators=[MinValueValidator(1.00), MaxValueValidator(4.00)]
    )
    
    # نظام التقييم
    grading_system = models.CharField(
        max_length=20,
        choices=GRADING_SYSTEMS,
        default='letter',
        verbose_name=_("Grading System"),
        help_text=_("The grading system used in this program")
    )
    
    semester_system = models.CharField(
        max_length=20,
        choices=SEMESTER_TYPES,
        default='semester',
        verbose_name=_("Academic Calendar System"),
        help_text=_("The type of academic calendar used in this program")
    )
    
    # إعدادات المقررات
    allow_course_repeat = models.BooleanField(
        default=True,
        verbose_name=_("Allow Course Repeat"),
        help_text=_("Whether students can repeat courses they have already passed")
    )
    max_course_repeats = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Maximum Course Repeats"),
        help_text=_("Maximum number of times a student can repeat a course"),
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    allow_course_withdrawal = models.BooleanField(
        default=True,
        verbose_name=_("Allow Course Withdrawal"),
        help_text=_("Whether students can withdraw from courses")
    )
    withdrawal_deadline_weeks = models.PositiveIntegerField(
        default=8,
        verbose_name=_("Withdrawal Deadline (Weeks)"),
        help_text=_("Number of weeks into the semester after which course withdrawal is not allowed"),
        validators=[MinValueValidator(1), MaxValueValidator(15)]
    )
    
    # التحقق من صحة المقررات
    enforce_prerequisites = models.BooleanField(
        default=True,
        verbose_name=_("Enforce Prerequisites"),
        help_text=_("Whether to strictly enforce course prerequisites")
    )
    allow_concurrent_prerequisites = models.BooleanField(
        default=False,
        verbose_name=_("Allow Concurrent Prerequisites"),
        help_text=_("Whether prerequisites can be taken concurrently with the course")
    )
    check_credit_limits = models.BooleanField(
        default=True,
        verbose_name=_("Check Credit Limits"),
        help_text=_("Whether to enforce minimum and maximum credit limits")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    class Meta:
        verbose_name = _("Program Settings")
        verbose_name_plural = _("Program Settings")
        indexes = [
            models.Index(fields=['program'], name='program_settings_idx'),
            models.Index(fields=['grading_system'], name='grading_system_idx'),
        ]

    def __str__(self):
        return f"Settings for {self.program.name}"

    def clean(self):
        """التحقق من صحة إعدادات البرنامج"""
        super().clean()
        
        if self.max_duration_years < self.standard_duration_years:
            raise ValidationError({
                'max_duration_years': _("Maximum duration cannot be less than standard duration")
            })
        
        if self.min_credits_per_semester > self.max_credits_per_semester:
            raise ValidationError({
                'min_credits_per_semester': _("Minimum credits cannot be more than maximum credits")
            })
        
        if self.summer_semester_enabled and self.max_summer_credits > self.max_credits_per_semester:
            raise ValidationError({
                'max_summer_credits': _("Maximum summer credits cannot exceed maximum regular semester credits")
            })

    def calculate_total_semesters(self):
        """حساب العدد الإجمالي للفصول الدراسية"""
        years = float(self.standard_duration_years)
        if self.semester_system == 'semester':
            semesters_per_year = 3 if self.summer_semester_enabled else 2
        elif self.semester_system == 'quarter':
            semesters_per_year = 4
        elif self.semester_system == 'trimester':
            semesters_per_year = 3
        else:
            semesters_per_year = 2
            
        return int(years * semesters_per_year)

    def validate_semester_credits(self, credits, semester_type='regular'):
        """التحقق من صحة عدد الساعات في الفصل"""
        if not self.check_credit_limits:
            return True
            
        if semester_type == 'summer':
            if not self.summer_semester_enabled:
                raise ValidationError(_('Summer semester is not enabled for this program'))
                
            if credits > self.max_summer_credits:
                raise ValidationError(
                    _("Summer semester credits cannot exceed %(max)s"),
                    params={'max': self.max_summer_credits}
                )
        else:
            if credits < self.min_credits_per_semester:
                raise ValidationError(
                    _("Regular semester credits cannot be less than %(min)s"),
                    params={'min': self.min_credits_per_semester}
                )
            if credits > self.max_credits_per_semester:
                raise ValidationError(
                    _("Regular semester credits cannot exceed %(max)s"),
                    params={'max': self.max_credits_per_semester}
                )
        return True
    
    def validate_course_registration(self, student, course, semester):
        """التحقق من صحة تسجيل الطالب للمقرر"""
        # التحقق من المتطلبات السابقة
        if self.enforce_prerequisites:
            from apps.academic.models import StudentGrade
            
            # الحصول على المتطلبات السابقة للمقرر
            prerequisites = course.prerequisites.all()
            if not prerequisites.exists():
                return True
                
            # التحقق من اجتياز الطالب للمتطلبات السابقة
            for prereq in prerequisites:
                # التحقق من وجود درجة ناجحة للمتطلب السابق
                passed_grade = StudentGrade.objects.filter(
                    student=student,
                    course=prereq,
                    is_passing=True
                ).exists()
                
                # التحقق من التسجيل المتزامن إذا كان مسموحًا
                concurrent_registration = False
                if self.allow_concurrent_prerequisites:
                    from apps.academic.models import CourseRegistration
                    concurrent_registration = CourseRegistration.objects.filter(
                        student=student,
                        course=prereq,
                        semester=semester,
                        status__in=['active', 'approved']
                    ).exists()
                
                if not passed_grade and not concurrent_registration:
                    return False, prereq.code
                    
        return True, None
    
    def validate_graduation_requirements(self, student):
        """التحقق من استيفاء متطلبات التخرج"""
        from apps.academic.models import StudentGrade
        
        # التحقق من المعدل التراكمي
        if student.cgpa < self.min_cgpa_required:
            return False, _('CGPA is below the minimum required for graduation')
        
        # التحقق من اجتياز جميع المقررات المطلوبة
        required_courses = ProgramCourse.objects.filter(
            program=self.program,
            is_required=True,
            status='active'
        ).values_list('course', flat=True)
        
        passed_courses = StudentGrade.objects.filter(
            student=student,
            course__in=required_courses,
            is_passing=True
        ).values_list('course', flat=True).distinct()
        
        missing_courses = set(required_courses) - set(passed_courses)
        if missing_courses:
            missing_course_codes = Course.objects.filter(id__in=missing_courses).values_list('code', flat=True)
            return False, _('Missing required courses: %s') % ', '.join(missing_course_codes)
        
        # التحقق من عدد الساعات المعتمدة الاختيارية
        active_study_plan = StudyPlan.objects.filter(
            program=self.program,
            is_active=True
        ).order_by('-effective_date').first()
        
        if active_study_plan:
            elective_credits_required = active_study_plan.elective_credits
            elective_credits_earned = StudentGrade.objects.filter(
                student=student,
                course__program_courses__program=self.program,
                course__program_courses__is_required=False,
                is_passing=True
            ).aggregate(Sum('course__credits'))['course__credits__sum'] or 0
            
            if elective_credits_earned < elective_credits_required:
                return False, _('Insufficient elective credits: %(earned)s/%(required)s') % {
                    'earned': elective_credits_earned,
                    'required': elective_credits_required
                }
        
        return True, _('All graduation requirements have been met')

class AcademicLevel(models.Model):
    """نموذج المستوى الدراسي"""
    
    program = models.ForeignKey(
        AcademicProgram,
        on_delete=models.CASCADE,
        related_name='levels',
        verbose_name=_("Academic Program")
    )
    
    level_number = models.PositiveIntegerField(
        verbose_name=_("Level Number"),
        help_text=_("Level number in the program (1, 2, 3, etc.)")
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Level Name"),
        help_text=_("Name of the academic level (e.g. Freshman, Sophomore, etc.)")
    )
    
    required_credits = models.PositiveIntegerField(
        verbose_name=_("Required Credits"),
        help_text=_("Required credits to complete this level")
    )
    
    min_cgpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=2.00,
        verbose_name=_("Minimum CGPA"),
        help_text=_("Minimum CGPA required to pass this level")
    )
    
    prerequisite_level = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_levels',
        verbose_name=_("Prerequisite Level"),
        help_text=_("Level that must be completed before this level")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Description of this academic level and its requirements")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this level is currently active in the program")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Academic Level")
        verbose_name_plural = _("Academic Levels")
        ordering = ['program', 'level_number']
        unique_together = [['program', 'level_number']]
        indexes = [
            models.Index(fields=['is_active'], name='level_active_idx'),
        ]

    def __str__(self):
        return f"{self.program.name} - {self.name} (Level {self.level_number})"
    
    def clean(self):
        """التحقق من صحة بيانات المستوى الدراسي"""
        super().clean()
        
        # التحقق من أن المستوى السابق له رقم مستوى أقل
        if self.prerequisite_level and self.prerequisite_level.level_number >= self.level_number:
            raise ValidationError({
                'prerequisite_level': _("Prerequisite level number must be less than this level's number")
            })
        
        # التحقق من أن المستوى السابق ينتمي إلى نفس البرنامج
        if self.prerequisite_level and self.prerequisite_level.program != self.program:
            raise ValidationError({
                'prerequisite_level': _("Prerequisite level must belong to the same program")
            })
    
    def save(self, *args, **kwargs):
        """حفظ المستوى الدراسي مع التحقق من صحة البيانات"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_total_credits(self):
        """حساب إجمالي الساعات المعتمدة للمقررات في هذا المستوى"""
        return self.semester_plans.aggregate(
            total_credits=Sum(models.F('semester_courses__course__credits'))
        )['total_credits'] or 0
    
    def get_semesters(self):
        """الحصول على الفصول الدراسية في هذا المستوى"""
        return self.semester_plans.all().order_by('year', 'semester_type')
    
    def get_courses(self):
        """الحصول على جميع المقررات في هذا المستوى"""
        from django.db.models import Prefetch
        
        return Course.objects.filter(
            semester_courses__semester_plan__academic_level=self
        ).distinct().prefetch_related(
            Prefetch('semester_courses', queryset=SemesterCourse.objects.filter(
                semester_plan__academic_level=self
            ))
        )


class AcademicLevelSemester(models.Model):
    """نموذج ربط المستويات الأكاديمية بالفصول الدراسية الفعلية"""
    
    academic_level = models.ForeignKey(
        AcademicLevel,
        on_delete=models.CASCADE,
        related_name='level_semesters',
        verbose_name=_("Academic Level")
    )
    
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        related_name='level_semesters',
        verbose_name=_("Academic Year")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='level_semesters',
        verbose_name=_("Semester")
    )
    
    cohort = models.CharField(
        max_length=20,
        verbose_name=_("Cohort"),
        help_text=_("Cohort identifier (e.g. 2025, 2026)")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    class Meta:
        verbose_name = _("Academic Level Semester")
        verbose_name_plural = _("Academic Level Semesters")
        unique_together = [['academic_level', 'semester', 'cohort']]
        ordering = ['academic_year', 'semester', 'academic_level']
        indexes = [
            models.Index(fields=['cohort'], name='cohort_idx'),
            models.Index(fields=['is_active'], name='level_semester_active_idx'),
        ]
    
    def __str__(self):
        return f"{self.academic_level} - {self.semester} ({self.cohort})"
    
    def clean(self):
        """التحقق من صحة بيانات ربط المستوى بالفصل"""
        super().clean()
        
        # التحقق من أن الفصل ينتمي إلى السنة الأكاديمية المحددة
        if self.semester.academic_year != self.academic_year:
            raise ValidationError({
                'semester': _("Semester must belong to the specified academic year")
            })
    
    def save(self, *args, **kwargs):
        """حفظ ربط المستوى بالفصل مع التحقق من صحة البيانات"""
        self.clean()
        super().save(*args, **kwargs)
    
    def get_semester_courses(self):
        """الحصول على مقررات الفصل الدراسي لهذا المستوى"""
        # الحصول على خطة دراسية نشطة للبرنامج
        active_study_plan = StudyPlan.objects.filter(
            program=self.academic_level.program,
            status='active'
        ).order_by('-effective_from').first()
        
        if not active_study_plan:
            return []
        
        # الحصول على خطة الفصل الدراسي المناسبة
        semester_plans = SemesterPlan.objects.filter(
            study_plan=active_study_plan,
            academic_level=self.academic_level,
            semester_type=self.semester.semester_type
        )
        
        if not semester_plans.exists():
            return []
        
        # الحصول على مقررات الفصل
        return SemesterCourse.objects.filter(
            semester_plan__in=semester_plans
        ).select_related('course', 'semester_plan')

