#!/bin/sh

apt-get update
apt-get install -y --no-install-recommends rsync

python3 -m pip install \
    --user --no-warn-script-location \
    tox wheel setuptools twine poetry \
    flake8 pytest pytest-timeout pytest-xdist mypy isort pylint \
    six requests websocket \
    paramiko \
    types-six types-urllib3 types-requests types-paramiko

rsync \
    --exclude '.tox' --exclude '__pycache__' --exclude '.mypy_cache' --exclude '.pytest_cache' --exclude '*.pyc' \
    --exclude 'docker.egg-info' --exclude '.coverage.*' \
    -v -a \
    /workspace/ /local/
