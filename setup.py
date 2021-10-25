from pathlib import Path

from setuptools import find_packages, setup


ROOT_DIRECTORY = Path(__file__).resolve().parent

description = "An easy solution for system/dotfile configuration"
readme = (ROOT_DIRECTORY / "README.md").read_text()
changelog = (ROOT_DIRECTORY / "CHANGELOG.md").read_text()
long_description = readme + "\n\n" + changelog

version = (ROOT_DIRECTORY / "instater" / "VERSION").read_text().strip()


DEV_REQUIRES = [
    "black==21.9b0",
    "coverage==6.0.2",
    "flake8==4.0.1",
    "flake8-bugbear==21.9.2",
    "isort==5.9.3",
    "mypy==0.910",
    "pytest==6.2.5",
    "pytest-cov==3.0.0",
    "twine==3.4.2",
]

setup(
    name="instater",
    version=version,
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
        "Jinja2==3.0.2",
        "PyYAML==6.0",
        "passlib==1.7.4",
        "rich==10.12.0",
    ],
    python_requires=">=3.7",
    extras_require={
        "dev": DEV_REQUIRES,
    },
    include_package_data=True,
)
