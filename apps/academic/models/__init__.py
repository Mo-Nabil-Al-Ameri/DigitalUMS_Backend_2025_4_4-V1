"""
حزمة النماذج للتطبيق الأكاديمي
تحتوي على نماذج إدارة العمليات الأكاديمية المختلفة
"""

from .academic_year import AcademicYear, Semester
from .admission import AdmissionApplication, Document
from .enrollment import StudentEnrollment, SemesterRegistration, CourseRegistration
from .course_management import CourseSection, CourseSectionSchedule, CourseInstructor
from .grading import Grade, GradeScale, GradeComponent, StudentGrade
from .academic_advising import AcademicAdvisor, AdvisingSession, AcademicWarning
from .graduation import GraduationApplication, GraduationRequirementCheck

__all__ = [
    'AcademicYear', 'Semester',
    'AdmissionApplication', 'Document',
    'StudentEnrollment', 'SemesterRegistration', 'CourseRegistration',
    'CourseSection', 'CourseSectionSchedule', 'CourseInstructor',
    'Grade', 'GradeScale', 'GradeComponent', 'StudentGrade',
    'AcademicAdvisor', 'AdvisingSession', 'AcademicWarning',
    'GraduationApplication', 'GraduationRequirementCheck',
]
