#!/usr/bin/env bash
# Запуск тестов в docker

. ./tools/common-functions.sh

docker ps -a -q -f status=exited | xargs --no-run-if-empty docker rm -v
docker-compose down | true

docker-compose up --abort-on-container-exit
check_exitcode_tests; exit_code=$?
docker-compose down | true
check_exitcode ${exit_code}
success "tests completed!"

