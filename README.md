# DSP Integration (Django + Celery)

1. `docker-compose up --build`
2. `poetry shell` (if not using Docker)
3. `python manage.py migrate`
4. Start worker: `celery -A dsp_integration.celery worker --loglevel=info`
5. Start beat: `celery -A dsp_integration.celery beat --loglevel=info`
6. (Optional) `python manage.py runserver` for Admin UI on :8000

## Adding a superuser for the Admin page
1. docker compose exec web sh
2. python manage.py createsuperuser
3. Enter username, email and password to use to login to http://0.0.0.0:8000/admin

### To create and run migrations on a models change
1. docker compose exec web python manage.py makemigrations submissions
2. docker compose exec web python manage.py migrate
3. docker compose restart web worker
