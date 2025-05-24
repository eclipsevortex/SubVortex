# syntax=docker/dockerfile:1.4

########################################
# Stage 0 — Build wheels using wheel-builder
########################################
FROM wheelbuilder AS wheels

WORKDIR /build

COPY ./subvortex/miner/metagraph/requirements.txt ./requirements.txt

RUN pip wheel -r requirements.txt -w /wheels \
    && rm -rf ~/.cache/pip

########################################
# Stage 1 — Final runtime image
########################################
FROM python:3.11-slim

# ---------- Metadata & Labels ----------
ARG MAINTAINER="subvortex.bt@gmail.com"
ARG VERSION="0.0.0"
ARG ROLE_VERSION="0.0.0"
ARG COMPONENT_VERSION="0.0.0"
LABEL maintainer=$MAINTAINER
LABEL version=$VERSION
LABEL validator.version=$ROLE_VERSION
LABEL validator.metagraph.version=$COMPONENT_VERSION

# ---------- Environment ----------
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 🧱 Copy only built wheels from Stage 0
COPY --from=wheels /wheels /tmp/wheels

# ✅ Only copy wheels and install, discard after
COPY --from=wheels /wheels /tmp/wheels
COPY ./subvortex/miner/metagraph/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels ~/.cache/pip

# 📁 Copy source code
COPY ./pyproject-miner.toml ./pyproject.toml
COPY ./subvortex/pyproject.toml ./subvortex/pyproject.toml
COPY ./subvortex/core ./subvortex/core
COPY ./subvortex/miner/version.py ./subvortex/miner/version.py
COPY ./subvortex/miner/core ./subvortex/miner/core
COPY ./subvortex/miner/metagraph/src ./subvortex/miner/metagraph/src
COPY ./subvortex/miner/metagraph/entrypoint.sh ./subvortex/miner/metagraph/entrypoint.sh
COPY ./subvortex/miner/metagraph/pyproject.toml ./subvortex/miner/metagraph/pyproject.toml

# 🧩 Install project (editable)
RUN pip install -e . \
    && rm -rf ~/.cache/pip

ENTRYPOINT ["/bin/bash", "./subvortex/miner/metagraph/entrypoint.sh"]
