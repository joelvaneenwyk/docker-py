# syntax=docker/dockerfile:1.4

ARG USERNAME=sphinx
ARG USER_ID=1000
ARG GROUP_ID=1000

ARG WORKSPACE_DIR="/src"

ARG PYTHON_VERSIONS="3.10.9 3.9.16 3.11.1 3.8.16 3.7.16 2.7.18 pypy3.9-7.3.11"

ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION} AS python_base

ARG USERNAME
ARG USER_ID
ARG GROUP_ID
ARG WORKSPACE_DIR
ARG PYTHON_VERSIONS

ENV DEBIAN_FRONTEND=noninteractive
ENV USERNAME=$USERNAME
ENV USER_ID=$USER_ID
ENV GROUP_ID=$GROUP_ID

RUN apt-get update \
    && apt-get install -y \
    bash sudo curl wget git

RUN addgroup --gid $GROUP_ID ${USERNAME} \
    && useradd --uid $USER_ID --gid $GROUP_ID -M ${USERNAME} \
    && usermod -aG sudo ${USERNAME}
RUN mkdir -p "/home/${USERNAME}" \
    && sudo chown -R ${USERNAME}:${USERNAME} "/home/${USERNAME}" \
    && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

ENV WORKSPACE_DIR="${WORKSPACE_DIR}"
RUN mkdir -p ${WORKSPACE_DIR} \
    && chown -R ${USERNAME}:${USERNAME} ${WORKSPACE_DIR}

USER ${USERNAME}

ENV HOME="/home/${USERNAME}"
ENV PYTHON_VERSIONS="${PYTHON_VERSIONS}"

WORKDIR ${WORKSPACE_DIR}
SHELL ["/bin/bash", "--login", "-c"]

RUN curl https://pyenv.run | bash \
    && echo 'export HOME="/home/${USERNAME}"' >>~/.bashrc \
    && echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.bashrc \
    && echo 'export PATH="$HOME/.local/bin:$PYENV_ROOT/bin:$PATH"' >>~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >>~/.bashrc

RUN source ~/.bashrc \
    && versions=($(echo "$PYTHON_VERSIONS" | tr ' ' '\n')) \
    && if [ ! ${#versions[@]} -eq 0 ]; then pyenv install "${versions[@]}"; fi

FROM python_base AS python_shell

ARG USERNAME

RUN source ~/.bashrc \
    && sudo apt-get update \
    && sudo apt-get install -y --no-install-recommends \
    build-essential procps curl file git \
    && bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
    && echo 'export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"' >>~/.bashrc

RUN source ~/.bashrc \
    && brew update \
    && brew install jandedobbeleer/oh-my-posh/oh-my-posh \
    && echo 'eval "$(oh-my-posh init bash)"'>>~/.bashrc

RUN source ~/.bashrc \
    && sudo apt-get update \
    && sudo apt-get install -y --no-install-recommends \
    curl \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN cargo install lsd
RUN echo 'alias ll="lsd -al"' >> ~/.bashrc

FROM python_shell AS python_docker

ARG USERNAME
ARG SETUPTOOLS_SCM_PRETEND_VERSION_DOCKER

RUN sudo apt-get update \
    && sudo apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release apt-transport-https \
    && sudo mkdir -m 0755 -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && sudo chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && sudo apt-get update \
    && sudo apt-get install -y --no-install-recommends \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

FROM python_docker AS python_docker_sdk
ARG USERNAME

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

RUN for python_version in $(pyenv versions --bare); do \
    eval "$(pyenv init -)" \
    && pyenv shell $python_version \
    && python -m pip install --upgrade pip virtualenv wheel tox pre-commit pipx; \
    done

# Add SSH keys and set permissions
ENV HOME="/home/${USERNAME}"
COPY ./tests/ssh-keys ${HOME}/.ssh
RUN sudo chmod -R 600 ${HOME}/.ssh

COPY --chown=${USER} . ./

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["bash"]
