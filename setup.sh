#!/bin/sh

if [ -x "$(command -v apt-get)" ]; then
    if sudo apt-get update; then
        sudo apt-get install -y --no-install-recommends rsync
    fi
fi

if [ ! -x "$(command -v pyenv)" ]; then
    # curl https://pyenv.run | bash
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    cd ~/.pyenv && src/configure && make -C src

    # shellcheck disable=SC2016
    {
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
    } >>~/.bashrc

    export PYENV_ROOT="$HOME/.pyenv"
    eval "$(pyenv init -)"
fi

if [ -x "$(command -v pyenv)" ]; then
    pyenv install --skip-existing 2.7.18 3.10.9
    pyenv local 3.10.9 2.7.18
    pyenv shell 3.10.9 2.7.18
fi

if [ ! -x "$(command -v poetry)" ]; then
    curl -sSL https://install.python-poetry.org | python3 -
fi

if [ -x "$(command -v poetry)" ]; then
    poetry install --only main
else
    python3 -m pip install \
        --user --no-warn-script-location \
        tox wheel setuptools twine poetry \
        flake8 pytest pytest-timeout pytest-xdist mypy isort pylint \
        six requests websocket \
        paramiko \
        types-six types-urllib3 types-requests types-paramiko
fi

if [ -e "/local" ]; then
    rsync \
        --exclude '.tox' --exclude '__pycache__' --exclude '.mypy_cache' --exclude '.pytest_cache' --exclude '*.pyc' \
        --exclude 'docker.egg-info' --exclude '.coverage.*' \
        -v -a \
        /workspace/ /local/
fi
