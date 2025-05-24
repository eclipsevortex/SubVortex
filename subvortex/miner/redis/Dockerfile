FROM redis:7.2.4-alpine

# ---------- Metadata & Labels ----------
ARG MAINTAINER="subvortex.bt@gmail.com"
ARG VERSION="0.0.0"
ARG ROLE_VERSION="0.0.0"
ARG COMPONENT_VERSION="0.0.0"
LABEL maintainer=$MAINTAINER
LABEL version=$VERSION
LABEL miner.version=$ROLE_VERSION
LABEL miner.redis.version=$COMPONENT_VERSION

# ---------- Environment ----------
ENV PYTHONUNBUFFERED=1

WORKDIR /data

# 📁 Copy source code
COPY ./subvortex/validator/redis/entrypoint.sh ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
