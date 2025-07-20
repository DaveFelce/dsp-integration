# DSP Integration (Django + Celery)

### Building and running the project
1. `docker compose up --build`

### Adding a superuser for the Admin page
1. `ddocker compose exec web sh`
2. `python manage.py createsuperuser`
3. Enter username, email and password to use to login to http://0.0.0.0:8000/admin

### View the tables to check end to end test results
1. http://0.0.0.0:8000/admin/submissions/dspentityqueue/
2. http://0.0.0.0:8000/admin/submissions/dspentityaudit/
3. http://0.0.0.0:8000/admin/django_celery_results/taskresult/

### To create and run migrations on a models change
1. `docker compose exec web python manage.py makemigrations submissions`
2. `docker compose exec web python manage.py migrate`
3. `docker compose restart web worker`

### running the mocked end to end test
1. `docker compose exec web python end2end_test.py`

### running the unit/integration tests
1. `docker compose exec web pytest`
