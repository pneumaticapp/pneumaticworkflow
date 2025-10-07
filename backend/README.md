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

### Installation
Open a terminal in the "backend" directory and run the following commands:
1. Start backend containers ``docker compose up -d``






### For developers

Quick server start 

```commandline
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py compilemessages
gunicorn src.asgi:application --workers 2 -k uvicorn.workers.UvicornWorker --worker-tmp-dir /dev/shm --bind 0.0.0.0:8001
```

If you need debug SQL queries, use this context manager:
```python
from src.logs.utils import log_sql
with log_sql():
   ... # code for debug here
```
After that, find "django_queries.log" in the project root

# Postgres

## How init Pneumatic database
*Need to be installed postgresql-client on host machine*

1. Save database export file to directory ``pneumatic-backend/database/backups/dump.sql``
2. (Optional) If database already exists need recreate with commands:
```commandline
docker exec -it pneumatic-postgres sh -c "dropdb -U postgres_user postgres_db && createdb -U postgres_user --owner postgres_user postgres_db"
```
3. Import data in the database 
```commandline
docker exec -it pneumatic-postgres sh -c "psql -U postgres_user -h localhost postgres_db < /backups/dump.sql"
```
4. Connect to database
```commandline
 docker exec -it pneumatic-postgres sh -c "psql -U postgres_user postgres_db"
```