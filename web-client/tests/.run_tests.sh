#!/usr/bin/env bash
docker-compose -f tests/docker-compose.test.yml up --build --abort-on-container-exit
# Записываем результат выполнения тестов в переменную, чтобы завершить текущий скрипт с таким же кодом
TESTS_EXIT_CODE=$?;

docker-compose -f tests/docker-compose.test.yml down -v

exit ${TESTS_EXIT_CODE}
