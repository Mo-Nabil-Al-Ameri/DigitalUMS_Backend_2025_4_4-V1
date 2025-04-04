import os
import environ
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# تحديد مسار المشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# تحميل المتغيرات البيئية
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# مفاتيح الأمان
SECRET_KEY = env("SECRET_KEY", default="your-default-secret-key")
DEBUG = env.bool("DEBUG", default=True)

# السماح بالمضيفين
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# التطبيقات المثبتة
INSTALLED_APPS = [
    # التطبيقات الافتراضية لـ Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # تطبيقات المشروع
    'apps.core.apps.CoreConfig',  # إضافة تطبيق core
    'apps.university'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # دعم الترجمة: Middleware الترجمة
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # إضافة processor الترجمة
            ],
        },
    },
]
ROOT_URLCONF = 'project.urls'

WSGI_APPLICATION = 'project.wsgi.application'

# إعدادات الترجمة واللغات
LANGUAGE_CODE = 'en'  # Default language: English

# إضافة اللغات المدعومة
LANGUAGES = [
    ('en', _('English')),  # English first as default
    ('ar', _('Arabic')),   # Arabic second
]

# تمكين ميزة الترجمة
USE_I18N = True

# تمكين تنسيق الأرقام والتاريخ حسب اللغة
USE_L10N = True

# مسارات ملفات الترجمة
LOCALE_PATHS = [
    os.path.join(BASE_DIR.parent, 'locale'),
]

# إعدادات إضافية للترجمة
LANGUAGE_COOKIE_NAME = 'django_language'  # اسم ملف تعريف ارتباط اللغة
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365  # مدة صلاحية ملف تعريف ارتباط اللغة (سنة)
LANGUAGE_COOKIE_DOMAIN = None  # نطاق ملف تعريف ارتباط اللغة
LANGUAGE_COOKIE_PATH = '/'  # مسار ملف تعريف ارتباط اللغة

# تكوين الكاش للترجمة
USE_I18N_CACHE = True  # تفعيل التخزين المؤقت للترجمة
I18N_CACHE_KEY_PREFIX = 'i18n'  # بادئة مفتاح التخزين المؤقت للترجمة
I18N_CACHE_TIMEOUT = 60 * 60 * 24  # مدة التخزين المؤقت للترجمة (24 ساعة)

# إعدادات تنسيق التاريخ والوقت
DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'Y-m-d H:i'
YEAR_MONTH_FORMAT = 'F Y'
MONTH_DAY_FORMAT = 'F j'
SHORT_DATE_FORMAT = 'Y-m-d'
SHORT_DATETIME_FORMAT = 'Y-m-d H:i'

# المنطقة الزمنية
TIME_ZONE = 'UTC'
USE_TZ = True

# إعدادات Celery
CELERY_BROKER_URL = env("CELERY_BROKER", default="redis://redis:6379/0")

# إعدادات الملفات الثابتة
STATIC_URL = 'static/'
MEDIA_URL = 'media/'

STATICFILES_DIRS = [BASE_DIR.parent / 'static']
MEDIA_ROOT = BASE_DIR.parent / 'media'

# إعدادات نظام الترقيم
# ==================

# إعدادات ترقيم الكليات
COLLEGE_NUMBERING_SETTINGS = {
    'min_number': 1,
    'max_number': 99,
    'number_width': 2,
    'number_prefix': '',
    'number_suffix': '',
    'separator': '-',
    'use_prefix': True
}

# إعدادات ترقيم الأقسام
DEPARTMENT_NUMBERING_SETTINGS = {
    'min_number': 1,
    'max_number': 99,
    'number_width': 2,
    'number_prefix': '',
    'number_suffix': '',
    'separator': '-',
    'use_prefix': True
}

# إعدادات ترقيم البرامج
PROGRAM_NUMBERING_SETTINGS = {
    'min_number': 1,
    'max_number': 999,
    'number_width': 3,
    'number_prefix': '',
    'number_suffix': '',
    'separator': '-',
    'use_prefix': True
}
