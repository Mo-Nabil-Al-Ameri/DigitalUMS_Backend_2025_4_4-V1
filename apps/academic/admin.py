"""
تسجيل نماذج التطبيق الأكاديمي في واجهة الإدارة
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    AcademicYear, Semester,
    AdmissionApplication, Document,
    StudentEnrollment, SemesterRegistration, CourseRegistration,
    CourseSection, CourseSectionSchedule, CourseInstructor,
    Grade, GradeScale, GradeComponent, StudentGrade,
    AcademicAdvisor, AdvisingSession, AcademicWarning,
    GraduationApplication, GraduationRequirementCheck,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)
    ordering = ('-start_date',)


class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 0


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'semester_type', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'semester_type', 'is_current')
    search_fields = ('name', 'academic_year__name')
    ordering = ('-academic_year__start_date', 'start_date')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'document_type', 'uploaded_by', 'upload_date', 'verified')
    list_filter = ('document_type', 'verified')
    search_fields = ('name', 'uploaded_by__username')
    ordering = ('-upload_date',)


@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'program', 'academic_year', 'semester', 'status', 'application_date')
    list_filter = ('status', 'academic_year', 'semester', 'program')
    search_fields = ('applicant__username', 'applicant__first_name', 'applicant__last_name')
    ordering = ('-application_date',)
    readonly_fields = ('application_date', 'score')
    fieldsets = (
        (None, {
            'fields': ('applicant', 'program', 'academic_year', 'semester', 'status')
        }),
        (_('Application Details'), {
            'fields': ('previous_education', 'gpa', 'personal_statement', 'score')
        }),
        (_('Review Information'), {
            'fields': ('reviewer', 'review_date', 'decision_date', 'notes')
        }),
    )


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'status', 'enrollment_date', 'expected_graduation')
    list_filter = ('status', 'program', 'academic_year')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name')
    ordering = ('-enrollment_date',)
    readonly_fields = ('enrollment_date',)


@admin.register(SemesterRegistration)
class SemesterRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'semester', 'status', 'total_credits')
    list_filter = ('status', 'academic_year', 'semester')
    search_fields = ('student__user__username', 'student__user__first_name', 'student__user__last_name')
    ordering = ('-registration_date',)
    readonly_fields = ('registration_date', 'total_credits')


@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ('semester_registration', 'course_section', 'status', 'registration_date')
    list_filter = ('status', 'semester_registration__semester')
    search_fields = ('semester_registration__student__user__username', 'course_section__course__name')
    ordering = ('-registration_date',)
    readonly_fields = ('registration_date',)


class CourseSectionScheduleInline(admin.TabularInline):
    model = CourseSectionSchedule
    extra = 0


class CourseInstructorInline(admin.TabularInline):
    model = CourseInstructor
    extra = 0


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'section_number', 'semester', 'status', 'capacity', 'enrolled_students')
    list_filter = ('status', 'semester', 'academic_year')
    search_fields = ('course__name', 'course__code', 'section_number')
    ordering = ('semester', 'course__code', 'section_number')
    inlines = [CourseSectionScheduleInline, CourseInstructorInline]


@admin.register(CourseSectionSchedule)
class CourseSectionScheduleAdmin(admin.ModelAdmin):
    list_display = ('course_section', 'day_of_week', 'start_time', 'end_time', 'location', 'schedule_type')
    list_filter = ('day_of_week', 'schedule_type', 'course_section__semester')
    search_fields = ('course_section__course__name', 'location')
    ordering = ('course_section', 'day_of_week', 'start_time')


@admin.register(CourseInstructor)
class CourseInstructorAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'course_section', 'role', 'assignment_date')
    list_filter = ('role', 'course_section__semester')
    search_fields = ('instructor__user__username', 'instructor__user__first_name', 'course_section__course__name')
    ordering = ('-assignment_date',)


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('name',)


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('letter', 'points', 'min_percent', 'max_percent', 'is_passing', 'scale')
    list_filter = ('scale', 'is_passing')
    search_fields = ('letter', 'description')
    ordering = ('scale', '-order')


@admin.register(GradeComponent)
class GradeComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_section', 'component_type', 'weight', 'max_score', 'due_date')
    list_filter = ('component_type', 'course_section__semester')
    search_fields = ('name', 'course_section__course__name')
    ordering = ('course_section', 'due_date')


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'grade', 'numeric_value', 'grade_points')
    list_filter = ('semester', 'grade__is_passing')
    search_fields = ('student__user__username', 'student__user__first_name', 'course__name')
    ordering = ('student', 'semester', 'course')
    readonly_fields = ('grade_points', 'graded_date', 'last_modified')


@admin.register(AcademicAdvisor)
class AcademicAdvisorAdmin(admin.ModelAdmin):
    list_display = ('faculty_member', 'department', 'max_students', 'is_active', 'start_date')
    list_filter = ('is_active', 'department')
    search_fields = ('faculty_member__user__username', 'faculty_member__user__first_name')
    ordering = ('department', 'faculty_member')


@admin.register(AdvisingSession)
class AdvisingSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'advisor', 'session_type', 'scheduled_date', 'status')
    list_filter = ('status', 'session_type')
    search_fields = ('student__user__username', 'student__user__first_name', 'advisor__user__username')
    ordering = ('-scheduled_date',)
    readonly_fields = ('created_date', 'completed_date')


@admin.register(AcademicWarning)
class AcademicWarningAdmin(admin.ModelAdmin):
    list_display = ('student', 'warning_type', 'semester', 'status', 'issue_date')
    list_filter = ('status', 'warning_type', 'semester')
    search_fields = ('student__user__username', 'student__user__first_name')
    ordering = ('-issue_date',)
    readonly_fields = ('issue_date', 'resolution_date')


@admin.register(GraduationApplication)
class GraduationApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'program', 'semester', 'status', 'expected_graduation_date')
    list_filter = ('status', 'semester', 'program')
    search_fields = ('student__user__username', 'student__user__first_name')
    ordering = ('-application_date',)
    readonly_fields = ('application_date', 'review_date', 'decision_date')


@admin.register(GraduationRequirementCheck)
class GraduationRequirementCheckAdmin(admin.ModelAdmin):
    list_display = ('application', 'is_eligible', 'total_credits_completed', 'current_cgpa', 'check_date')
    list_filter = ('is_eligible', 'all_required_courses_completed', 'has_active_academic_warnings')
    search_fields = ('application__student__user__username', 'application__student__user__first_name')
    ordering = ('-check_date',)
    readonly_fields = ('check_date', 'last_updated')
    fieldsets = (
        (None, {
            'fields': ('application', 'check_date', 'last_updated', 'is_eligible')
        }),
        (_('Credit Requirements'), {
            'fields': ('total_credits_required', 'total_credits_completed')
        }),
        (_('GPA Requirements'), {
            'fields': ('min_cgpa_required', 'current_cgpa')
        }),
        (_('Course Requirements'), {
            'fields': ('all_required_courses_completed', 'all_course_groups_requirements_met')
        }),
        (_('Other Requirements'), {
            'fields': ('has_active_academic_warnings', 'has_financial_holds')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
    )
