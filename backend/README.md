# Pneumatic backend

### Configuration
Create a file ".env" with the following values in "backend" directory:
```shell
BACKEND_URL=http://localhost:8001
FRONTEND_URL=http://localhost
FORMS_URL=http://form.localhost

SSL=no        # Disable using https
ENVIRONMENT=Development
LANGUAGE_CODE=en # Allowed langs: en, fr, de, es, ru
CAPTCHA=no   # Disable using captcha in forms
ANALYTICS=no # Disable any analytics integrations
BILLING=no   # Disable stripe integration
SIGNUP=yes   # Disable signup page
MS_AUTH=no   # Disable Microsoft auth
GOOGLE_AUTH=no # Disable Google auth
SSO_AUTH=no   # Disable SSO Auth0 auth
EMAIL=no      # Disable send emails
EMAIL_PROVIDER=
AI=no         # Disable AI template generation
AI_PROVIDER=
PUSH=no       # Disable push notifications
PUSH_PROVIDER=
STORAGE=no    # Disable file storage
STORAGE_PROVIDER=

DJANGO_DEBUG='yes'
ENABLE_LOGGING='yes'
ADMIN_PATH='admin'
DJANGO_SECRET_KEY=django_secret_django_secret_django_secret
DJANGO_SETTINGS_MODULE=src.settings
AUTH_REDIS_URL=redis://:redis_password@localhost:6379/1
CACHE_REDIS_URL=redis://:redis_password@localhost:6379/0
CHANNELS_REDIS_URL=redis://:redis_password@localhost:6379/2
SESSION_REDIS_URL=redis://:redis_password@localhost:6379/3
CELERY_BROKER_URL=amqp://rabbitmq_user:rabbitmq_password@localhost:5672
ALLOWED_HOSTS=
CORS_ORIGIN_ALLOW_ALL='no'
CORS_ALLOW_CREDENTIALS='yes'
CORS_ORIGIN_WHITELIST=
```

## Installation
### Linux

The instructions are multi-platform, but examples are given for Linux Debian / Ubuntu.
Open a terminal in the "backend" directory and run the following commands:
1. Start backend containers ``docker compose up -d``.
2. Install [pyenv](https://github.com/pyenv/pyenv).
3. Use pyenv to install Python version Python 3.7.5. Command: ``pyenv install 3.7.5``.
4. Set Python 3.7.5 as the default version. Command: ``pyenv local 3.7.5``.
5. Verify the Python version with the command ``python --version``.
6. Install the poetry package manager with the command: ``pip install --upgrade pip && pip install poetry``
7. Create a virtual environment and install the project dependencies. Command: ``poetry install && poetry shell``
8. Display the virtual environment directory with the command: ``poetry env info``. Use this directory when creating scripts in your IDE.

### Project Initialization
#### Initializing a clean database
1. Apply database migrations with the command: ``python manage.py migrate``.
2. Create static files with the command: ``python manage.py collectstatic --no-input``
3. Create a superuser account for accessing the admin interface. Specify the user's email and password in the command: ``python manage.py create_superuser <email> <password>``
4. Start the server. Command: ``gunicorn src.asgi:application --workers 2 -k uvicorn.workers.UvicornWorker --worker-tmp-dir /dev/shm --bind 0.0.0.0:8001``.
5. Open the admin interface in your browser and log in: [http://localhost:8001/admin/](http://localhost:8001/admin/) (Use the email and password from step 3).
6. Open the user interface in your browser and log in: [http://localhost](http://localhost)(Use the email and password from step 3).

#### Initializing an Existing Database
1. Place the database dump file named ``dump.sql`` in the ``pneumaticworkflow/postgres/backups`` directory. 
2. Recreate the pneumatic database with the command: ``docker exec -it pneumatic-postgres sh -c "dropdb -U postgres_user postgres_db && createdb -U postgres_user --owner postgres_user postgres_db"``.
3. Load the dump file into the database with the command: ``docker exec -it pneumatic-postgres sh -c "psql -U postgres_user -h localhost postgres_db < /backups/dump.sql"``. This process will take several minutes.
4. (Optional). Connect to the database and verify the schema. Command: ``docker exec -it pneumatic-postgres sh -c "psql -U postgres_user postgres_db"``

### Windows
Will be added later


### Debugging
If you need debug SQL queries, use this context manager:
```python
from src.logs.utils import log_sql
with log_sql():
   ... # code for debug here
```
After that, find "django_queries.log" in the "backend" directory.