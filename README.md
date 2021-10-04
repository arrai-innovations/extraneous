# extraneous

Find extraneous pip packages not listed in your requirements.txt or as a sub-dependency.

![extraneous logo](https://docs.arrai-dev.com/extraneous/readme/extraneous.png)

[![PYPI](https://img.shields.io/pypi/v/extraneous?style=for-the-badge)](https://pypi.org/project/extraneous/)

###### main

![Tests](https://docs.arrai-dev.com/extraneous/main.python39.svg) [![Coverage](https://docs.arrai-dev.com/extraneous/main.python39.coverage.svg)](https://docs.arrai-dev.com/extraneous/htmlcov_main_python39/)

![Tests](https://docs.arrai-dev.com/extraneous/main.python38.svg) [![Coverage](https://docs.arrai-dev.com/extraneous/main.python38.coverage.svg)](https://docs.arrai-dev.com/extraneous/htmlcov_main_python38/)

![Tests](https://docs.arrai-dev.com/extraneous/main.python37.svg) [![Coverage](https://docs.arrai-dev.com/extraneous/main.python37.coverage.svg)](https://docs.arrai-dev.com/extraneous/htmlcov_main_python37/)

![Tests](https://docs.arrai-dev.com/extraneous/main.python36.svg) [![Coverage](https://docs.arrai-dev.com/extraneous/main.python36.coverage.svg)](https://docs.arrai-dev.com/extraneous/htmlcov_main_python36/)

![Flake8](https://docs.arrai-dev.com/extraneous/main.flake8.svg)

## Install

```console
$ pip install extraneous
```

## Help

```console
$ extraneous.py -h
usage: extraneous.py [-h] [--verbose] [--include paths] [--exclude names]
[--full]

Identifies packages that are installed but not defined in requirements files.
Prints the 'pip uninstall' command that removes these extraneous packages and
any non-common dependencies. Looks for packages matching '*requirements*.txt'
in the current working directory.

optional arguments:
-h, --help
    show this help message and exit
--verbose, -v
    Prints installed site-package folders and requirements files.
--include paths, -i paths
    Additional directories to look for '*requirements*.txt' files in.
--exclude names, -e names
    Package names to not consider extraneous. ['extraneous', 'pipdeptree',
     'pip', 'setuptools'] are not considered extraneous packages.
--full, -f
    Allows ['extraneous', 'pipdeptree', 'pip', 'setuptools'] as extraneous
     packages.
```

## Example output

```console
$ extraneous.py
extraneous packages:
        smbprotocol
uninstall via:
        pip uninstall -y smbprotocol cryptography dataclasses pyspnego
```

## Development

1. Clone the repo.
2. Setup and activate a new venv.
3. Install `requirements.txt` into your venv.

## Testing

1. Install `test_requirements.txt` into your venv.
2. Run `$ python setup.py test`.

## Build and Publish

1. Install `build_requirements.txt` into your venv.
2. Run `$ python setup.py bdist_wheel`.
3. Run `$ twine upload dist/*t`.
