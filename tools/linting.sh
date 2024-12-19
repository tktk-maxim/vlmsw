#!/usr/bin/env bash

. ./tools/common-functions.sh

IMAGE="docker.vizorlabs.ru/dockers/python_linters:main"

echo "========================================="
info "run mypy ..."
docker run --user 1000:1000 --rm -v $(pwd):/src "${IMAGE}" bash -c "cd /src && mypy ."; exit_code=$?; check_exitcode ${exit_code}
success "end mypy"
echo "========================================="

echo "========================================="
info "run black ..."
docker run --user 1000:1000 --rm -v $(pwd):/src "${IMAGE}" bash -c "cd /src && black ."; exit_code=$?; check_exitcode ${exit_code}
success "end black"
echo "========================================="

echo "========================================="
info "run isort ..."
docker run --user 1000:1000 --rm -v $(pwd):/src "${IMAGE}" bash -c "cd /src && isort ."; exit_code=$?; check_exitcode ${exit_code}
success "end isort"
echo "========================================="

echo "========================================="
info "run flake8 ..."
docker run --user 1000:1000 --rm -v $(pwd):/src "${IMAGE}" bash -c "cd /src && flake8 ."; exit_code=$?; check_exitcode ${exit_code}
success "end flake8"
echo "========================================="

echo "========================================="
info "run pylint ..."
docker run --user 1000:1000 --rm -v $(pwd):/src "${IMAGE}" bash -c "cd /src && pylint --recursive=y ."; exit_code=$?; check_exitcode ${exit_code}
success "end pylint"
echo "========================================="
