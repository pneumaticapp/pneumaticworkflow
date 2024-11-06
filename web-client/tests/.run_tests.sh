#!/usr/bin/env bash
docker-compose -f tests/docker-compose.test.yml up --build --abort-on-container-exit
# We write the result of the tests to a variable to complete the current script with the same code
TESTS_EXIT_CODE=$?;

docker-compose -f tests/docker-compose.test.yml down -v

exit ${TESTS_EXIT_CODE}
