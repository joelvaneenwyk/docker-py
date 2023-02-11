#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

_sudo() {
    if [ -x "$(command -v apt-get)" ]; then
        sudo "$@"
    else
        "$@"
    fi
}

_sudo chown vscode .tox || true

if [ -x "$(command -v apt-get)" ]; then
    if _sudo apt-get update; then
        _sudo apt-get install -y --no-install-recommends rsync
    fi
fi

if [ -x "$(command -v pyenv)" ]; then
    echo "Found 'pyenv' installation: $(command -v pyenv)"
else
    # curl https://pyenv.run | bash
    if [ ! -e "$HOME/.pyenv" ]; then
        git clone https://github.com/pyenv/pyenv.git "$HOME/.pyenv"
        (
            cd "$HOME/.pyenv" || true
            src/configure
            make -C src
        )
    fi

    # shellcheck disable=SC2016
    {
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
    } >>"$HOME/.bashrc"

    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    echo "Initialized 'pyenv' environment: '${PYENV_ROOT}'"
fi

if [ -x "$(command -v pyenv)" ]; then
    versions=("3.10.9" "3.9.16" "3.11.1" "3.8.16" "3.7.16" "2.7.18" "pypy3.9-7.3.11")
    pyenv install --skip-existing "${versions[@]}"

    if [ ! -e "$SCRIPT_DIR/.python-version" ]; then
        pyenv global "${versions[@]}"
        pyenv local "${versions[@]}"
        pyenv shell "${versions[@]}"
    fi
fi

if [ ! -x "$(command -v poetry)" ]; then
    curl -sSL https://install.python-poetry.org | python3 -
fi

if [ -x "$(command -v poetry)" ]; then
    poetry install --only main
fi

if [ -x "$(command -v python)" ]; then
    python -m pip install -U wheel pip setuptools
    python -m pip install \
        --user --no-warn-script-location \
        -r "$SCRIPT_DIR/requirements-dev.txt"
fi

if [ -e "/local" ]; then
    rsync \
        --exclude '.tox' --exclude '__pycache__' --exclude '.mypy_cache' --exclude '.pytest_cache' --exclude '*.pyc' \
        --exclude 'docker.egg-info' --exclude '.coverage.*' \
        -v -a \
        /workspace/ /local/
fi
