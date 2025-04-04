"""
نماذج التقييم ودرجات الطلاب
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class GradeScale(models.Model):
    """نموذج مقياس الدرجات"""
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Scale Name")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Is Default")
    )
    
    class Meta:
        verbose_name = _("Grade Scale")
        verbose_name_plural = _("Grade Scales")
        
    def __str__(self):
        return self.name
    
    def clean(self):
        """التحقق من صحة البيانات"""
        if self.is_default:
            # التأكد من عدم وجود مقياس آخر افتراضي
            default_scales = GradeScale.objects.filter(is_default=True)
            if self.pk:
                default_scales = default_scales.exclude(pk=self.pk)
            if default_scales.exists():
                raise ValidationError({
                    'is_default': _("Another grade scale is already set as default")
                })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default(cls):
        """الحصول على مقياس الدرجات الافتراضي"""
        try:
            return cls.objects.get(is_default=True)
        except cls.DoesNotExist:
            return None


class Grade(models.Model):
    """نموذج الدرجة"""
    
    scale = models.ForeignKey(
        'GradeScale',
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_("Grade Scale")
    )
    
    letter = models.CharField(
        max_length=5,
        verbose_name=_("Letter Grade")
    )
    
    description = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name=_("Grade Points")
    )
    
    min_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Minimum Percentage")
    )
    
    max_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Maximum Percentage")
    )
    
    is_passing = models.BooleanField(
        default=True,
        verbose_name=_("Is Passing Grade")
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Order")
    )
    
    class Meta:
        verbose_name = _("Grade")
        verbose_name_plural = _("Grades")
        ordering = ['scale', '-order']
        unique_together = [['scale', 'letter']]
        
    def __str__(self):
        return f"{self.letter} ({self.points})"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        if self.min_percent and self.max_percent and self.min_percent > self.max_percent:
            raise ValidationError({
                'max_percent': _("Maximum percentage must be greater than minimum percentage")
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_grade_for_value(cls, numeric_value, scale=None):
        """الحصول على الدرجة المناسبة للقيمة العددية"""
        if scale is None:
            scale = GradeScale.get_default()
            if scale is None:
                return None
        
        try:
            return cls.objects.get(
                scale=scale,
                min_percent__lte=numeric_value,
                max_percent__gte=numeric_value
            )
        except cls.DoesNotExist:
            return None


class GradeComponent(models.Model):
    """نموذج مكون الدرجة"""
    
    COMPONENT_TYPES = [
        ('exam', _('Exam')),
        ('quiz', _('Quiz')),
        ('assignment', _('Assignment')),
        ('project', _('Project')),
        ('participation', _('Participation')),
        ('midterm', _('Midterm Exam')),
        ('final', _('Final Exam')),
        ('lab', _('Lab Work')),
        ('presentation', _('Presentation')),
        ('other', _('Other')),
    ]
    
    course_section = models.ForeignKey(
        'academic.CourseSection',
        on_delete=models.CASCADE,
        related_name='grade_components',
        verbose_name=_("Course Section")
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Component Name")
    )
    
    component_type = models.CharField(
        max_length=20,
        choices=COMPONENT_TYPES,
        verbose_name=_("Component Type")
    )
    
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Weight (%)")
    )
    
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name=_("Maximum Score")
    )
    
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Due Date")
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description")
    )
    
    is_required = models.BooleanField(
        default=True,
        verbose_name=_("Is Required")
    )
    
    class Meta:
        verbose_name = _("Grade Component")
        verbose_name_plural = _("Grade Components")
        ordering = ['course_section', 'due_date']
        
    def __str__(self):
        return f"{self.course_section} - {self.name} ({self.weight}%)"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        # التحقق من أن مجموع الأوزان لا يتجاوز 100%
        total_weight = GradeComponent.objects.filter(
            course_section=self.course_section
        ).exclude(pk=self.pk).aggregate(
            total=models.Sum('weight')
        )['total'] or 0
        
        if total_weight + self.weight > 100:
            raise ValidationError({
                'weight': _("Total weight of all components cannot exceed 100%. Current total: {total}%").format(
                    total=total_weight
                )
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class StudentGrade(models.Model):
    """نموذج درجة الطالب"""
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_("Student")
    )
    
    course = models.ForeignKey(
        'departments.Course',
        on_delete=models.CASCADE,
        related_name='student_grades',
        verbose_name=_("Course")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='student_grades',
        verbose_name=_("Semester")
    )
    
    grade = models.ForeignKey(
        'Grade',
        on_delete=models.CASCADE,
        related_name='student_grades',
        verbose_name=_("Grade")
    )
    
    numeric_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Numeric Value")
    )
    
    grade_points = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        verbose_name=_("Grade Points")
    )
    
    is_included_in_gpa = models.BooleanField(
        default=True,
        verbose_name=_("Is Included in GPA")
    )
    
    graded_by = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_courses',
        verbose_name=_("Graded By")
    )
    
    graded_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Graded Date")
    )
    
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Modified")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Student Grade")
        verbose_name_plural = _("Student Grades")
        unique_together = [['student', 'course', 'semester']]
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.course.name}: {self.grade.letter}"
    
    def save(self, *args, **kwargs):
        # تحديث نقاط الدرجة من الدرجة المحددة
        self.grade_points = self.grade.points
        
        super().save(*args, **kwargs)
        
        # تحديث المعدل التراكمي للطالب
        self.student.update_gpa()
    
    @classmethod
    def calculate_gpa(cls, student, semester=None):
        """حساب المعدل الفصلي أو التراكمي للطالب"""
        grades_query = cls.objects.filter(
            student=student,
            is_included_in_gpa=True
        )
        
        if semester:
            grades_query = grades_query.filter(semester=semester)
        
        total_points = 0
        total_credits = 0
        
        for grade in grades_query:
            credits = grade.course.credit_hours
            total_points += float(grade.grade_points) * credits
            total_credits += credits
        
        if total_credits == 0:
            return 0.0
            
        return round(total_points / total_credits, 2)


class ComponentScore(models.Model):
    """نموذج درجة مكون التقييم"""
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='component_scores',
        verbose_name=_("Student")
    )
    
    component = models.ForeignKey(
        'GradeComponent',
        on_delete=models.CASCADE,
        related_name='student_scores',
        verbose_name=_("Grade Component")
    )
    
    score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name=_("Score")
    )
    
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Percentage")
    )
    
    weighted_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Weighted Score")
    )
    
    submitted_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Submitted Date")
    )
    
    graded_by = models.ForeignKey(
        'users.FacultyMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_components',
        verbose_name=_("Graded By")
    )
    
    graded_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Graded Date")
    )
    
    feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Feedback")
    )
    
    class Meta:
        verbose_name = _("Component Score")
        verbose_name_plural = _("Component Scores")
        unique_together = [['student', 'component']]
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.component.name}: {self.score}/{self.component.max_score}"
    
    def save(self, *args, **kwargs):
        # حساب النسبة المئوية
        if self.component.max_score > 0:
            self.percentage = (self.score / self.component.max_score) * 100
        else:
            self.percentage = 0
        
        # حساب الدرجة الموزونة
        self.weighted_score = (self.percentage / 100) * self.component.weight
        
        super().save(*args, **kwargs)
        
        # تحديث الدرجة الإجمالية للطالب في المقرر
        self.calculate_course_grade()
    
    def calculate_course_grade(self):
        """حساب الدرجة الإجمالية للطالب في المقرر"""
        # الحصول على جميع درجات مكونات التقييم للطالب في هذا المقرر
        course_section = self.component.course_section
        components = GradeComponent.objects.filter(course_section=course_section)
        
        total_weighted_score = 0
        total_weight = 0
        
        for component in components:
            try:
                score = ComponentScore.objects.get(
                    student=self.student,
                    component=component
                )
                total_weighted_score += float(score.weighted_score)
                total_weight += float(component.weight)
            except ComponentScore.DoesNotExist:
                # إذا لم يتم تقييم المكون بعد، نتخطاه
                pass
        
        # إذا تم تقييم جميع المكونات المطلوبة، نقوم بتحديث الدرجة الإجمالية
        required_components = components.filter(is_required=True)
        scored_required = ComponentScore.objects.filter(
            student=self.student,
            component__in=required_components
        ).count()
        
        if scored_required == required_components.count() and total_weight > 0:
            # حساب الدرجة الإجمالية
            final_score = total_weighted_score
            
            # الحصول على الدرجة المناسبة
            grade = Grade.get_grade_for_value(final_score)
            
            if grade:
                # تحديث أو إنشاء درجة الطالب في المقرر
                StudentGrade.objects.update_or_create(
                    student=self.student,
                    course=course_section.course,
                    semester=course_section.semester,
                    defaults={
                        'grade': grade,
                        'numeric_value': final_score,
                        'grade_points': grade.points,
                        'graded_by': self.graded_by
                    }
                )
