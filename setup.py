from pathlib import Path

from setuptools import find_packages, setup

ROOT_DIRECTORY = Path(__file__).resolve().parent

description = "An easy solution for system/dotfile configuration"
readme = (ROOT_DIRECTORY / "README.md").read_text()
changelog = (ROOT_DIRECTORY / "CHANGELOG.md").read_text()
long_description = readme + "\n\n" + changelog

DEV_REQUIRES = [
    "black==23.3.0",
    "coverage==7.2.3",
    "flake8==6.0.0; python_version >= '3.8'",
    "flake8==5.0.4; python_version < '3.8'",
    "flake8-bugbear==23.3.23; python_version >= '3.8'",
    "flake8-bugbear==23.3.12; python_version < '3.8'",
    "isort==5.12.0; python_version >= '3.8'",
    "isort==5.11.5; python_version < '3.8'",
    "mypy==1.2.0",
    "pytest==7.3.1",
    "pytest-cov==4.0.0",
    "twine==4.0.2",
]

setup(
    name="instater",
    version="0.13.1",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    author="Naya Verdier",
    url="https://github.com/nayaverdier/instater",
    license="MIT",
    packages=find_packages(exclude=("tests",)),
    entry_points={"console_scripts": ["instater = instater.cli:main"]},
    install_requires=[
        "Jinja2~=3.0",
        "PyYAML~=6.0",
        "passlib~=1.7",
        "rich>=10.12.0",
        "importlib-metadata>=1.0.0; python_version < '3.8'",
    ],
    python_requires=">=3.7",
    extras_require={
        "dev": DEV_REQUIRES,
    },
    include_package_data=True,
)
