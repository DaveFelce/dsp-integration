# DSP Integration (Django + Celery)

### Building and running the project
1. `docker compose up --build`

### Adding a superuser for the Admin page
1. `docker compose exec web sh`
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

## Technologies used and the reasoning behind them
1. **Django**: A high-level Python web framework that encourages rapid development and clean, pragmatic design.
2. **Celery**: An asynchronous task queue/job queue based on distributed message passing, used for handling background tasks.
3. **PostgreSQL**: A powerful, open-source object-relational database system, chosen for its robustness and scalability.
4. **Docker**: A platform for developing, shipping, and running applications in containers, ensuring consistency across different environments.
5. **Redis**: An in-memory data structure store, used as a message broker for Celery to handle task queues efficiently.
6. **pytest**: A testing framework for Python that makes it easy to write simple and scalable test cases.
7. **Django Admin**: A built-in feature of Django that provides a web-based interface for managing application data, making it easy to view and manipulate database records.
8. **Django Celery Results**: An extension for Django that stores the results of Celery tasks in the database, allowing for easy tracking and management of task outcomes.

## TODO
1. Write unit tests. At the moment, only integration tests are written.
2. Write a LOT more tests, especially using tests for the Celery tasks, testing things like:
   - Task retries
   - Task failures
   - Task timeouts
   - The task logic covering the dependency graph

## High level architecture diagram

```text
                          +---------------------+
                          |    Producer         |
                          |  (Enqueues jobs)    |
                          +----------+----------+
                                     |
                                     v
   +────────────────────────────────────────────────────+
   |                    PostgreSQL                      |
   |  +────────────────┐   +────────────────────────┐   |
   |  | dsp_entity_    |   | dsp_entity_audit       |   |
   |  |   queue        |   | (audit trail of all reqs)  |
   |  +────────────────┘   +────────────────────────┘   |
   +────────────────────────────────────────────────────+
                |                      ^
                |                      |
                v                      |
          +------------+               |
          |   Redis    |<--------------+
          |  (Broker)  |
          +------------+
                |
     +----------+----------+
     |                     |
     v                     v
+--------+           +-----------+
| Worker |           |   Beat    |
|(submit_entity)     |(polling)  |
+--------+           +-----------+
     |                     |
     v                     v
POST /v1/{entity}    GET /v1/{entity}/{id}/status
     |                     |
     v                     v
+----------------------------------------------+
|            Third-Party DSP API               |
|      (Rate-limited to 40 req/min)            |
+----------------------------------------------+
