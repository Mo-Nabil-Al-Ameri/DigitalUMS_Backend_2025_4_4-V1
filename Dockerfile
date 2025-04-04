# setup server
# 1: اعداد الحاوية و تثبيت Python 3.13
FROM python:3.13-slim-bullseye

# 2: ضبط اعدادات البيئة 
ENV PYTHONUNBUFFERED 1

# 3: تحديث ال kernal و تثبيت المكتبات المطلوبة
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4: انشاء مجلد المشروع 
WORKDIR /app

# 5 : نسخ ملف المتطلبات الخاصة بالمشروع  
COPY requirements.txt /app/requirements.txt

# 6: تثبيت المكتبات المطلوبة
RUN pip install -r /app/requirements.txt

# 7: نسخ الملفات الخاصة بالمشروع الى docker 
COPY . /app/
# # فتح المنفذ 8000 لتشغيل Django
# EXPOSE 8000

# # تشغيل المايجريشن ثم تشغيل السيرفر
# CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
