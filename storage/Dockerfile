FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-interaction --no-ansi --no-root --only=main \
    && rm -rf $POETRY_CACHE_DIR

COPY . .

ENV PYTHONPATH=/app

CMD ["sh", "-c", "poetry run alembic -c src/shared_kernel/database/alembic.ini upgrade head && poetry run python -m src.main"]
