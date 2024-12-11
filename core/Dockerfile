FROM python:3.7

# Install Internationalization requirements
RUN apt-get update && \
    apt-get -y install gettext

# postgresql client for execute psql command
RUN apt-get update && apt-get -y install postgresql-client

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first

RUN pip install poetry==1.5.1
RUN mkdir /pneumatic_backend
WORKDIR /pneumatic_backend

COPY ./pyproject.toml ./poetry.lock /pneumatic_backend/
RUN poetry config virtualenvs.create false && \
    poetry install --without dev --no-root --no-interaction

ADD . /pneumatic_backend/