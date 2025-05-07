# syntax=docker/dockerfile:1.4

FROM python:3.11-slim AS builder

WORKDIR /build

# Install only necessary system libraries (minimal footprint)
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  libssl-dev \
  libffi-dev \
  libpcap-dev \
  libnfnetlink-dev \
  libnetfilter-queue-dev \
  python3-dev \
  pkg-config && \
  curl https://sh.rustup.rs -sSf | sh -s -- -y --profile=minimal && \
  rm -rf /var/lib/apt/lists/*

ENV CFLAGS="-I/usr/include/libnetfilter_queue"
ENV PATH="/root/.cargo/bin:$PATH"