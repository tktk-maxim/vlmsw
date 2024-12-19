#!/usr/bin/env bash

DEFAULT_MODULE_PATH="/service/.venv/lib/python3.12.3/site-packages"


info() {
  msg=$1
  printf "\033[0;34mINFO: ${msg}\033[0m\n"
}

error() {
  msg=$1
  printf "\033[0;31mERROR: ${msg}\033[0m\n"
}

success() {
  msg=$1
  printf "\033[0;32mSUCCESS: ${msg}\033[0m\n"
}

check_exitcode() {
  # Проверяет код выхода из программы/функции.
  # прекратить выполнение скрипта, если exitcode != 0
  exitcode=$1
  info  "process done with exit code ${exitcode}"
  if [ "${exitcode}" != "0" ]
  then
    error "process failed with exit code ${exitcode}"
    exit 1
  else
    success "process success complete"
  fi
}

get_branch_name(){
  # получить название текущей ветки git
  echo "$(git symbolic-ref -q --short HEAD || git describe --all)"
}

get_image_tag(){
  # формирование тэга для docker image исходя из текущей ветки или тэга
  # если передать SEND_BRANCH=$1 - тэг будет задан исходя из переданного значения
  # иначе тэг будет взят из текущей ветки git
  SEND_BRANCH=${1}
  if [ -z "${SEND_BRANCH}" ]; then
    BRANCH=$(get_branch_name)
  else
    BRANCH=${SEND_BRANCH}
  fi

  # формируем имя тэга из ветки
  TAG="${BRANCH}"
  TAG=$(echo "${TAG}" | tr '[:upper:]' '[:lower:]')
  echo "${TAG}"
}

get_image_name(){
  # формирование имени для docker image исходя из текущей ветки или тэга
  SEND_BRANCH=${1}
  IMAGE_NAME=${2}

  # формируем имя тэга из ветки
  TAG=$(get_image_tag "${SEND_BRANCH}")
  RESULT_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
  echo "${RESULT_IMAGE_NAME}"
}


create_name_container_downloaded_models(){
  # сгенерировать уникальное название контейнера для загружаемых моделей
  CONTAINER_NAME="downloads_models_$(uuidgen)"
  echo "${CONTAINER_NAME}"
}

get_container_id_downloaded_models(){
  # получить ID контейнера с загруженными моделями на основании уникального имени контейнера
  NAME=$1
  CONTAINER_ID=$(docker ps -aqf "name=${NAME}")
  echo "${CONTAINER_ID}"
}

raise_empty_variable(){
  # вызвать ошибку в случае, если переменная пуста
  var_name="${1}"
  var_value=$(eval echo "\$${var_name}")
  if test -z "${var_value}"
  then
    error "${var_name} is empty, value: '${var_value}'. See --help"
    exit 1
  fi
}

load_environ(){
  # загрузка переменных из файла .env
  CURRENT_DIR="$(dirname $(realpath $0))"/../
  cd "${CURRENT_DIR}" || exit

  set -o allexport
  . ./.env
  set +o allexport
}


build_help()
{
    info "Building docker image script"
    echo
    info "Usage: ./build.sh -target <target> [-tag <tag>] [options]"
    echo
    info "args:"
    info "-target (required) - specify a target build stage"
    info "  Allowed targets:"
    info "    development         - image for development"
    info "    obfuscated          - image with obfuscated source code"
    info "    tests               - image with obfuscated source code and included tests and assets"
    info "    base-gpu-tests      - image with source code and included tests and assets for base-gpu-tests"
    info "    production          - image with obfuscated source code and included not converted ml models"
    echo
    info "-tag (optional) - image tag. By default for current branch: $(get_branch_name)"
    echo
    info "Options (optional) - options for docker build: https://docs.docker.com/reference/cli/docker/image/build/#options"
    echo
    info "For example:"
    info "1) build development image with main tag:                  ./build.sh -target=development -tag=main"
    info "2) build tests image with dev tag:                         ./build.sh -target=tests -tag=dev"
    info "3) build production image with default tag ($(get_branch_name)):    ./build.sh -target=production"
    info "4) build tests image without cache:                        ./build.sh -target=tests --no-cache"
    echo
}

test_help()
{
  info "Running test script with docker"
  echo
  info "Usage: ./tests.sh [-tag <tag>] [-spec-tests <specific tests path>]"
  echo
  info "args:"
  info "-tag (optional)           - image tag. By default for current branch: $(get_branch_name)"
  info "-spec-tests (optional)    - specific tests"
  echo
  info "For example:"
  info "1) run tests over ${IMAGE_NAME}:main:\n  ./tests.sh -tag=main\n"
  info "2) run tests over ${IMAGE_NAME}:$(get_branch_name):\n  ./tests.sh\n"
  info "3) run tests over ${IMAGE_NAME}:$(get_branch_name) for specific msv3 tests kolaes avangard (base-gpu tests):\n  ./tests.sh -spec-tests=kolaes,avangard\n"
  info "4) run tests over ${IMAGE_NAME}:$(get_branch_name) for specific tests detector and ocr:\n  ./tests.sh -spec-tests=detector.py,ocr.py\n"

  echo
}

push_help() {
  info "Push docker image to registry"
  echo
  info "Usage: ./push.sh [-tag <tag>]"
  echo
  info "args:"
  info "-tag (optional)    - image tag. By default for current branch: $(get_branch_name)"
  info "For example:"
  info "1) push image ${IMAGE_NAME}:main:           ./push.sh -tag=main"
  info "2) push image ${IMAGE_NAME}:$(get_branch_name):      ./push.sh"
  echo
}

validate_help()
{
  info "Running msv3 categories validation with docker"
  echo
  info "Usage: ./validate.sh [-tag <tag>]"
  echo
  info "args:"
  info "-tag (optional)    - image tag. By default for current branch: $(get_branch_name)"
  info "For example:"
  info "1) run validate over ${IMAGE_NAME}:main:           ./validate.sh -tag=main"
  info "2) run validate over ${IMAGE_NAME}:$(get_branch_name):      ./validate.sh"
  echo
}

obfuscate_help()
{
  info "Script to obfuscate the source code inside the docker image"
  echo
  info "Usage: ./obfuscate.sh <module_path> <module_name>"
  echo
  info "args:"
  info "- module_path            - path to module directory. default: ${DEFAULT_MODULE_PATH}"
  info "- module_name (required) - the name of the module in the specified directory"
  info "For example: ./obfuscate.sh vuka"
  echo
}

# Функция для парсинга аргументов
parse_args() {
    local target=""
    local tag=""
    local spec_tests=""
    local docker_options=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -target=*)
                target="${1#*=}"
                shift
                ;;
            -tag=*)
                tag="${1#*=}"
                shift
                ;;
            -spec-tests=*)
                spec_tests="${1#*=}"
                shift
                ;;
            --*)  # Обработка всех Docker-специфичных опций
                docker_options+=" $1"
                if [[ "$2" != "" && "$2" != --* && "$2" != -* ]]; then
                    docker_options+="=$2"
                    shift
                fi
                shift
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    echo "$target|$tag|$spec_tests|$docker_options"
}

parse_help() {
    script_name=$(basename "$0")
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                case $script_name in
                    build.sh)
                        build_help
                        ;;
                    tests.sh)
                        test_help
                        ;;
                    validate.sh)
                        validate_help
                        ;;
                    obfuscate.sh)
                        obfuscate_help
                        ;;
                    push.sh)
                        push_help
                        ;;
                    *)
                        echo "No help available for this script."
                        ;;
                esac
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
}

check_exitcode_tests(){
  # Получаем все контейнеры, управляемые текущим проектом docker-compose
  container_ids=$(docker-compose ps --all --quiet)

  # Проверяем, что список контейнеров не пуст
  if [ -z "$container_ids" ]; then
      echo "No containers found."
      exit 1
  fi

  # Перебираем каждый контейнер
  for id in $container_ids; do
      # Получаем код выхода для каждого контейнера
      exit_code=$(docker inspect --format '{{ .State.ExitCode }}' $id)
      
      # Проверяем, что код выхода не равен нулю
      if [ "$exit_code" -ne 0 ]; then
          # Дополнительно проверяем имя контейнера
          container_name=$(docker inspect --format '{{ .Name }}' $id)
          container_name="${container_name:1}" # Удаляем слэш в начале имени

          # Проверяем, что имя контейнера соответствует 'inference'
          if [[ "$container_name" == "${CONTAINER_NAME}" ]]; then
              error "Container $container_name with ID $id failed with exit code $exit_code"
              exit 1
          fi
      fi
  done
}

load_environ
parse_help "$@"

# Парсинг аргументов
IFS='|' read TARGET TAG SPEC_TESTS DOCKER_OPTIONS <<< "$(parse_args "$@")"