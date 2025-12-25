# Pneumatic backend

### Configuration
Create a file ".env" with the following values in "backend" directory:
```shell
BACKEND_URL=http://localhost:8001
FRONTEND_URL=http://localhost
FORMS_URL=http://form.localhost
ENVIRONMENT=Development
ENABLE_LOGGING=yes
DJANGO_DEBUG=yes
DJANGO_SETTINGS_MODULE=src.settings
DJANGO_SECRET_KEY=django_secret_django_secret_django_secret
POSTGRES_HOST=localhost
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
POSTGRES_DB=postgres_db
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
9. Install pre-commit hooks. Command: ``pre-commit install``

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
Open PowerShell in the backend directory and run the following commands:
1. Start the backend containers: ``docker compose up -d``.
2. Download and install Git Bash: ``https://git-scm.com/downloads``.
3. Download and install Python 3.7.5  ``https://www.python.org/downloads/release/python-375/``. During installation, make sure to check “Add Python to PATH.”
4. Verify that Python is installed: ``python --version``.
5. Install Poetry 1.5.1 by running the following command in PowerShell: ``$env:POETRY_VERSION="1.5.1"; (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -``
6. To get started you need to add Poetry's bit directory –C:\Users\{username}\AppData\Roaming\Python\Scripts– to your PATH. Replace {username} with your actual Windows username.
7. Verify your Poetry installation by running ``poetry --version`` in PowerShell.
8. Add the path to Poetry to ~/.bashrc by running the command: ``if ! grep -q "export PATH.*poetry" ~/.bashrc; then echo 'export PATH="$PATH:/c/Users/{username}/AppData/Roaming/Python/Scripts"' >> ~/.bashrc; fi && source ~/.bashrc``. Make sure to replace {username} with your actual Windows username.
9. Check you have the correct version of Poetry by running ``poetry --version`` in Git Bash.
10. Create a virtual environment and install project dependancies(``poetry install && poetry shell``).
11. To view the virtual environment directory, run the command ``poetry env info``. That's the directory you need to use when developing scripts in your IDE.


## Testing
Pytest requires the environment variables from the .env file. The easiest way to run tests is to set up an action in your IDE. Command ``pytest -vv .``

## Debugging
If you need debug SQL queries, use this context manager:
```python
from src.logs.utils import log_sql
with log_sql():
   ... # code for debug here
```
After that, find "django_queries.log" in the "backend" directory.