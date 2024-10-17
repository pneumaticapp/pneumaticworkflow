FROM python:3.7

RUN apt-get update && \
    pip install --upgrade pip && \
    pip install poetry==1.5.1

COPY ./pyproject.toml ./poetry.lock /tmp/
RUN cd /tmp && \
    poetry config virtualenvs.create false && \
    poetry install --with dev --no-root --no-interaction

WORKDIR /pneumatic_backend
