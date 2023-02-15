# syntax=docker/dockerfile:2

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y bash

# Add SSH keys and set permissions
COPY ./tests/ssh-keys /root/.ssh
RUN chmod -R 600 /root/.ssh

ENV HOME="/root"
ENV PATH="${PATH}:$HOME/.local/bin"

WORKDIR /src

RUN python -m pip install -U pip

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-test.txt ./requirements-test.txt
RUN pip install --no-cache-dir -r requirements-test.txt

ARG DEV_MODE=0
ENV PYENV_ROOT="$HOME/.pyenv"
ENV PATH="${PATH}:$PYENV_ROOT/bin"
ENV PY_VERSIONS="3.10.9 3.9.16 3.11.1 3.8.16 3.7.16 2.7.18 pypy3.9-7.3.11"

RUN curl https://pyenv.run | bash \
    && echo 'export PYENV_ROOT="$HOME/.pyenv"' >>"$HOME/.bashrc" \
    && echo 'export PATH="$PYENV_ROOT/bin:$PATH"'>>"$HOME/.bashrc" \
    && echo 'eval "$(pyenv init -)"'>>"$HOME/.bashrc" \
    && eval "$(pyenv init -)"

SHELL ["/bin/bash", "-c"]
RUN if [ ! $DEV_MODE = 0 ]; then \
      versions=($(echo "$PY_VERSIONS" | tr ' ' '\n')); \
      pyenv install "${versions[@]}"; \
      pyenv global "${versions[@]}"; \
      pyenv local "${versions[@]}"; \
      pyenv shell "${versions[@]}"; \
    fi

COPY . ./
ARG SETUPTOOLS_SCM_PRETEND_VERSION_DOCKER
# RUN pip install --no-cache-dir .
RUN pip install tox

RUN mkdir /workspace
WORKDIR /workspace

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["bash"]
