from setuptools import setup, find_packages

setup(
    name="tiktokmaxim_vlmsw",  # Имя пакета (должно быть уникальным на PyPI)
    version="0.1.1",  # Версия
    author="Max",
    author_email="masya3_03@mail.com",
    description="Краткое описание вашей библиотеки",
    long_description="dsds",
    long_description_content_type="text/markdown",
    url="https://github.com/tktk-maxim/vlmsw",  # Ссылка на репозиторий
    packages=find_packages(),  # Автоматический поиск пакетов
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",  # Минимальная версия Python
    install_requires=[],  # Зависимости, если есть
)