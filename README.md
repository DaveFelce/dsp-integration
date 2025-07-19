# DSP Integration (Django + Celery)

1. `docker-compose up --build`
2. `poetry shell` (if not using Docker)
3. `python manage.py migrate`
4. Start worker: `celery -A dsp_integration.celery worker --loglevel=info`
5. Start beat: `celery -A dsp_integration.celery beat --loglevel=info`
6. (Optional) `python manage.py runserver` for Admin UI on :8000
