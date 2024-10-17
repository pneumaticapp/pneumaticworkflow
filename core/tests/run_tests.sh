#!/bin/sh
docker-compose -f docker-compose.yml up -d --build pneumatic_postgres
docker-compose -f docker-compose.yml up --build pneumatic_backend;
TESTS_EXIT_CODE=$(docker wait pneumatic_backend)
docker-compose down -v
exit ${TESTS_EXIT_CODE}
