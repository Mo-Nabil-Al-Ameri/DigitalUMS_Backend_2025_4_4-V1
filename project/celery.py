import os
from celery import Celery

# ضبط Django كإعداد افتراضي لـ Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery("project")

# تحميل الإعدادات من Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# اكتشاف المهام داخل التطبيقات
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
