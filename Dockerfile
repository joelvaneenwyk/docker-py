# syntax=docker/dockerfile:2

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y bash

# Add SSH keys and set permissions
COPY ./tests/ssh-keys /root/.ssh
RUN chmod -R 600 /root/.ssh

ARG username=sphinx
ARG uid=1000
ARG gid=1000
RUN addgroup --gid $gid ${username} \
    && useradd --uid $uid --gid $gid -M ${username}

USER ${username}

ENV HOME="/root"
ENV PATH="${PATH}:$HOME/.local/bin"

WORKDIR /src

RUN python -m pip install --no-cache-dir --upgrade pip

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

ARG SETUPTOOLS_SCM_PRETEND_VERSION_DOCKER
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

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["bash"]
