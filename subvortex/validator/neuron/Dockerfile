# syntax=docker/dockerfile:1.4

########################################
# Stage 0 — Build wheels using wheel-builder
########################################
FROM wheelbuilder AS wheels

WORKDIR /build

COPY ./subvortex/validator/neuron/requirements.txt ./requirements.txt

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
LABEL validator.neuron.version=$COMPONENT_VERSION

# ---------- Environment ----------
ENV PYTHONUNBUFFERED=1
ARG SUBVORTEX_OBSERVER_TYPE=file
ENV SV_OBSERVER_TYPE=${SUBVORTEX_OBSERVER_TYPE}

# ✅ Install required runtime libraries
RUN apt-get update && apt-get install -y \
    libnfnetlink0 \
    libnetfilter-queue1 \
    iptables \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 🧱 Copy only built wheels from Stage 0
COPY --from=wheels /wheels /tmp/wheels

# ✅ Only copy wheels and install, discard after
COPY --from=wheels /wheels /tmp/wheels
COPY ./subvortex/validator/neuron/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --find-links=/tmp/wheels -r requirements.txt \
    && rm -rf /tmp/wheels ~/.cache/pip

# 📁 Copy source code
COPY ./pyproject-validator.toml ./pyproject.toml
COPY ./subvortex/pyproject.toml ./subvortex/pyproject.toml
COPY ./subvortex/core ./subvortex/core
COPY ./subvortex/validator/version.py ./subvortex/validator/version.py
COPY ./subvortex/validator/core ./subvortex/validator/core
COPY ./subvortex/validator/neuron/src ./subvortex/validator/neuron/src
COPY ./subvortex/validator/neuron/entrypoint.sh ./subvortex/validator/neuron/entrypoint.sh
COPY ./subvortex/validator/neuron/pyproject.toml ./subvortex/validator/neuron/pyproject.toml

# 🧩 Install project (editable)
RUN pip install "./subvortex/validator/neuron[observer-${SV_OBSERVER_TYPE}]" \
    && pip install -e . \
    && rm -rf ~/.cache/pip

ENTRYPOINT ["/bin/bash", "./subvortex/validator/neuron/entrypoint.sh"]
