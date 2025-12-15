FROM python:3.7.11-bullseye

LABEL org.opencontainers.image.title="Pneumatic API" \
      org.opencontainers.image.source="https://github.com/pneumaticapp/pneumaticworkflow/backend" \
      org.opencontainers.image.url="https://www.pneumatic.app" \
      org.opencontainers.image.authors="support@pneumatic.app" \
      org.opencontainers.image.vendor="Pneumatic Software Inc." \
      org.opencontainers.image.documentation="https://github.com/pneumaticapp/pneumaticworkflow/wiki" \
      org.opencontainers.image.licenses="Apache-2.0"

# Install Internationalization requirements
RUN apt-get update && \
    apt-get -y install gettext

# postgresql client for execute psql command
RUN apt-get update && apt-get -y install postgresql-client

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first

RUN pip install poetry==1.5.1

COPY ./pyproject.toml ./poetry.lock /tmp/

WORKDIR /pneumatic_backend
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root --no-interaction --directory /tmp
