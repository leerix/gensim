#!/bin/bash
set -e

platform=linux
if [[ "$(uname)" == "Darwin" ]]; then
    platform=mac
fi

pip install -e '.[test]'
pip install tox
tox -e flake8
tox -e docs
tox -e py39-$platform
