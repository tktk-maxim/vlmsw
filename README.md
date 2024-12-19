# vizorlabs-model-storage-wrapper vlmsw

Содержит функции для работы с реестром моделей. Позволяет загружать и скачивать модели из сервиса по хранению моделей.

Сервис оболочкой, которого является данный пакет: https://gitlab.vizorlabs.ru/severstal/model-storage


> **WARNING**: Рекомендуется установка при помощи poetry с изолированной виртуальной средой (см. установка с poetry)!

### Установка


#### Установка с poetry
1. Установить poetry
```shell
curl -sSL https://install.python-poetry.org | python3 -
poetry config virtualenvs.in-project true
```
2. Установить pyenv
```shell
git clone --depth=1 https://github.com/pyenv/pyenv.git ~/.pyenv

# for bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# for zsh
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```

3. Установить локальную python version
```shell
pyenv install 3.12.1 && pyenv local 3.12.1
```
4. Активировать виртуальную среду для проекта
```shell
poetry shell
```
5. Установить все зависимости, указанные в pyproject.toml
```shell
poetry install
```

После указанных шагов в директории с проектом будет создана виртуальное окружение с указанной версией python и всеми пакетами.
Для удобства работы в pycharm необходимо добавить конфигурацию с использованием данной виртуальной среды `.venv`
