#!/bin/sh

docker-compose rm -f
docker-compose up -d --build "$@"
