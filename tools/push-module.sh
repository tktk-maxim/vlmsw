#!/usr/bin/env bash

# Скрипт для изменения версии пакета, сборки и отправки в pypi
# 1) если ветка=tag (например v1.0.0), имя пакета=package
#  Версия пакета становится как в теге:
#  package-v1.0.0
# 2) если ветка=dev, и текущая версия в pyproject.toml=v1.0.0, имя пакета=package, hash commit=4168ac0
#  К текущей версии добавляется имя ветки, префикс релиза (rc0/post0) и hash commit
# 1 В случае отсутствия версии в pypi - добавляем rc0: package-v1.0.0rc0.dev.4168ac0
# 2 В случае присутствия версии в pypi - добавляем post0: package-v1.0.0post0.dev.4168ac0


function search_key(){
  # поиск значения в pyproject.toml секции [tool.poetry]
  local KEY=$1
  echo $(sed -nr "/^\[tool.poetry\]/ { :l /^${KEY}[ ]*=/ { s/[^=]*=[ ]*//; p; q;}; n; b l;}" ./pyproject.toml) | tr -d '"'
}

function get_line_num(){
  # получить номер строки из pyproject.toml в соответствии с переданной строкой
  local EXPRESSION=$1
  echo $(grep -n -m 1 "${EXPRESSION}" ./pyproject.toml | cut -f1 -d ":")
}

function replace_underscores() {
  local NAME=$1
  echo "$1" | tr '-' '_'
}


# поиск версии пакета в pypi.
# 1 В случае отсутствия версии - добавляем rc0. package_name=v1.0.0rc0+my_custom_name_branch.4168ac0
# 2 В случае присутствия версии - добавляем post0. package_name=v1.0.0post0+my_custom_name_branch.4168ac0
function set_prefix_version() {
  PACKAGE_NAME=$1
  SEARCH_VERSION=$2

  VERSIONS=$(echo "$(pip install ${PACKAGE_NAME}== --index-url=https://pip.vizorlabs.ru/simple 2>&1 >/dev/null)" | awk -F ":" '{print $3}')
  IFS=', ' read -r -a array <<< $(echo $VERSIONS)
  PREFIX="rc0"

  for index in "${!array[@]}"
  do
      if [[ ${array[index]} = "${SEARCH_VERSION}" ]]
      then
          PREFIX="post0";
      fi
  done

  echo "${PREFIX}"
}


function upload() {
  local VERSION=$1

  version_line=$(get_line_num $(search_key "version"))
  echo "change version $(search_key "version") to ${VERSION}"

  sed -i "${version_line}s/.*/version = '${VERSION}'/" ./pyproject.toml

  poetry build
  poetry config repositories.vizorlabs-pypi https://pip.vizorlabs.ru
  poetry config http-basic.vizorlabs-pypi "${PIP_USERNAME}" "${PIP_PASSWORD}"
  poetry publish -r vizorlabs-pypi
  echo -e "Upload ${NAME} package ver:${VERSION}"
}


if [ -n "${CI_COMMIT_TAG}" ]; then
  upload "${CI_COMMIT_TAG}"
else
  BRANCH_NAME="${CI_COMMIT_REF_SLUG//[-._]/}"    # delete -._
  BRANCH_NAME="${BRANCH_NAME,,}"                 # set lower case
  COMMIT_SHA=$(git rev-parse --short HEAD)
  CURRENT_VERSION=$(search_key "version")

  # <post0> or <rc0> prefix
  PREFIX=$(set_prefix_version $(search_key "name") $(search_key "version"))

  NEW_VERSION="${CURRENT_VERSION}${PREFIX}+${BRANCH_NAME}.${COMMIT_SHA}"

  upload "${NEW_VERSION}"
fi
