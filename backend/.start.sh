#!/bin/sh
python ./manage.py migrate
# wsgi
#/usr/local/bin/gunicorn src.wsgi:application --bind 0.0.0.0:8000

# asgi with websockets
gunicorn src.asgi:application --workers 1 -k uvicorn.workers.UvicornWorker --worker-tmp-dir /dev/shm