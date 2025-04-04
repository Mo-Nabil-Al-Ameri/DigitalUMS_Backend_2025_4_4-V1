"""
نماذج القبول والوثائق المطلوبة
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Document(models.Model):
    """نموذج الوثيقة"""
    
    DOCUMENT_TYPES = [
        ('id', _('ID Card/Passport')),
        ('certificate', _('Academic Certificate')),
        ('transcript', _('Academic Transcript')),
        ('photo', _('Personal Photo')),
        ('recommendation', _('Recommendation Letter')),
        ('cv', _('CV/Resume')),
        ('other', _('Other Document')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Document Name")
    )
    
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        verbose_name=_("Document Type")
    )
    
    file = models.FileField(
        upload_to='documents/',
        verbose_name=_("Document File")
    )
    
    uploaded_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='uploaded_documents',
        verbose_name=_("Uploaded By")
    )
    
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Upload Date")
    )
    
    verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified")
    )
    
    verified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents',
        verbose_name=_("Verified By")
    )
    
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verification Date")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-upload_date']
        
    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"
    
    def verify(self, verified_by):
        """تأكيد صحة الوثيقة"""
        self.verified = True
        self.verified_by = verified_by
        self.verification_date = timezone.now()
        self.save()


class AdmissionApplication(models.Model):
    """نموذج طلب القبول في البرنامج"""
    
    APPLICATION_STATUS = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('additional_info', _('Additional Information Required')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('canceled', _('Canceled')),
    ]
    
    applicant = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='admission_applications',
        verbose_name=_("Applicant")
    )
    
    program = models.ForeignKey(
        'departments.AcademicProgram',
        on_delete=models.CASCADE,
        related_name='admission_applications',
        verbose_name=_("Academic Program")
    )
    
    academic_year = models.ForeignKey(
        'academic.AcademicYear',
        on_delete=models.CASCADE,
        related_name='admission_applications',
        verbose_name=_("Academic Year")
    )
    
    semester = models.ForeignKey(
        'academic.Semester',
        on_delete=models.CASCADE,
        related_name='admission_applications',
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
    
    previous_education = models.TextField(
        verbose_name=_("Previous Education")
    )
    
    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name=_("GPA")
    )
    
    documents = models.ManyToManyField(
        'academic.Document',
        related_name='admission_applications',
        verbose_name=_("Documents")
    )
    
    personal_statement = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Personal Statement")
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes")
    )
    
    reviewer = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
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
    
    # تستخدم لتحديد الأولوية في القبول
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Admission Score")
    )
    
    class Meta:
        verbose_name = _("Admission Application")
        verbose_name_plural = _("Admission Applications")
        ordering = ['-application_date']
        
    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.program.name} ({self.get_status_display()})"
    
    def submit(self):
        """تقديم الطلب"""
        if self.status == 'draft':
            self.status = 'submitted'
            self.save()
            return True
        return False
    
    def start_review(self, reviewer):
        """بدء مراجعة الطلب"""
        if self.status == 'submitted':
            self.status = 'under_review'
            self.reviewer = reviewer
            self.review_date = timezone.now()
            self.save()
            return True
        return False
    
    def request_additional_info(self):
        """طلب معلومات إضافية"""
        if self.status in ['submitted', 'under_review']:
            self.status = 'additional_info'
            self.save()
            return True
        return False
    
    def approve(self):
        """الموافقة على الطلب"""
        if self.status in ['submitted', 'under_review']:
            self.status = 'approved'
            self.decision_date = timezone.now()
            self.save()
            return True
        return False
    
    def reject(self):
        """رفض الطلب"""
        if self.status in ['submitted', 'under_review', 'additional_info']:
            self.status = 'rejected'
            self.decision_date = timezone.now()
            self.save()
            return True
        return False
    
    def cancel(self):
        """إلغاء الطلب"""
        if self.status not in ['approved', 'rejected', 'canceled']:
            self.status = 'canceled'
            self.save()
            return True
        return False
    
    def calculate_score(self):
        """حساب درجة القبول"""
        # يمكن تخصيص هذه الدالة حسب معايير القبول في الجامعة
        # مثال بسيط: 70% من المعدل التراكمي + 30% من تقييم الوثائق
        
        # حساب درجة المعدل التراكمي (على مقياس 100)
        gpa_score = float(self.gpa) * 25  # تحويل المعدل من 4 إلى 100
        
        # حساب درجة الوثائق (افتراضياً 80 من 100)
        docs_score = 80
        
        # الدرجة النهائية
        final_score = (gpa_score * 0.7) + (docs_score * 0.3)
        
        self.score = final_score
        self.save(update_fields=['score'])
        return final_score
    
    def approve_and_enroll(self, study_plan=None, advisor=None):
        """الموافقة على طلب القبول وتسجيل الطالب في البرنامج"""
        from django.utils import timezone
        from users.models import Student
        from academic.models import StudentEnrollment
        
        if not self.approve():
            return False, "لا يمكن الموافقة على الطلب في حالته الحالية"
        
        # تحويل نوع المستخدم إلى طالب
        user = self.applicant
        user.user_type = 'student'
        user.save()
        
        # إنشاء حساب طالب
        student = Student.objects.create(
            user=user,
            student_id=self._generate_student_id(),
            program=self.program,
            study_plan=study_plan or self.program.active_study_plan,
            level=self.program.levels.filter(level_number=1).first(),
            enrollment_date=timezone.now().date(),
            expected_graduation=self._calculate_expected_graduation(),
            study_mode='full_time',
            status='active',
        )
        
        # تسجيل الطالب في البرنامج
        enrollment = StudentEnrollment.objects.create(
            student=student,
            program=self.program,
            study_plan=student.study_plan,
            academic_year=self.academic_year,
            semester=self.semester,
            status='active',
            advisor=advisor,
            expected_graduation=student.expected_graduation
        )
        
        return student, enrollment
    
    def _generate_student_id(self):
        """توليد رقم طالب جديد"""
        # نموذج للرقم: سنة القبول + رمز البرنامج + رقم تسلسلي
        year = str(self.academic_year.start_date.year)[-2:]
        program_code = str(self.program.code).zfill(3)
        
        # آخر رقم تسلسلي في البرنامج للسنة الحالية
        from users.models import Student
        last_student = Student.objects.filter(
            student_id__startswith=f"{year}{program_code}"
        ).order_by('-student_id').first()
        
        if last_student:
            # استخراج الرقم التسلسلي وزيادته
            sequence = int(last_student.student_id[-4:]) + 1
        else:
            sequence = 1
            
        return f"{year}{program_code}{str(sequence).zfill(4)}"
    
    def _calculate_expected_graduation(self):
        """حساب تاريخ التخرج المتوقع"""
        from datetime import timedelta
        import math
        
        # تحويل المدة إلى أيام
        duration_years = float(self.program.settings.standard_duration_years)
        days = int(duration_years * 365.25)
        return self.semester.start_date + timedelta(days=days)
