# Build the subtensor
FROM ubuntu:22.04 as subtensor

SHELL ["/bin/bash", "-c"]

# Install git and other dependencies
RUN apt-get update && \
  apt-get install -y curl build-essential protobuf-compiler clang git && \
  rm -rf /var/lib/apt/lists/*

# Clone the Git repository into the container
RUN git clone https://github.com/opentensor/subtensor.git

WORKDIR /subtensor

# Checkout mmain branch
RUN git checkout main

RUN git pull origin main

# Install cargo and Rust
RUN set -o pipefail && curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Init subtensor
RUN ./scripts/init.sh

# Define default values for arguments
ENV CHAIN_SPEC="raw_localspec.json"

# show backtraces
ENV RUST_BACKTRACE 1

# Building substrate binary
RUN cargo build --release --features "pow-faucet runtime-benchmarks"

# Building chainspec
RUN ./target/release/node-subtensor build-spec --disable-default-bootnode --raw --chain local > $CHAIN_SPEC

# Purging previous state
RUN ./target/release/node-subtensor purge-chain -y --base-path /tmp/bob --chain="$CHAIN_SPEC" >/dev/null 2>&1
RUN ./target/release/node-subtensor purge-chain -y --base-path /tmp/alice --chain="$CHAIN_SPEC" >/dev/null 2>&1


FROM python:3.10

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y net-tools nodejs npm && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g pm2

# Copy subnet source
COPY ./neurons /SubVortex/neurons
COPY ./subnet /SubVortex/subnet
COPY ./setup.py /SubVortex
COPY ./requirements.txt /SubVortex
COPY ./VERSION /SubVortex
COPY ./README.md /SubVortex

# Go to SubVortex directory
WORKDIR /SubVortex

# Install project dependencies
RUN pip install -r requirements.txt

# Install the source
RUN pip install -e .

# Go to the root directory
WORKDIR /

# Subtensor
COPY --from=subtensor /subtensor /subtensor
COPY ./scripts/subtensor/docker/scripts/entrypoint.sh ./subtensor/entrypoint.sh 

# Miner
COPY ./scripts/subnet/docker/miner/entrypoint-miner.sh ./SubVortex/entrypoint.sh 

# Global
COPY ./scripts/subnet/docker/miner/entrypoint.sh .

# Define default values for arguments
ARG NETUID=1
ARG WALLET_NAME=miner-1
ARG WALLET_HOTKEY=miner-1-1
ARG WALLET_PATH=/.bittensor/wallets
ARG SUBTENSOR_NETWORK=local
ARG SUBTENSOR_CHAIN_ENDPOINT
ARG SUBTENSOR_NODE_ID
ARG AXON_PORT=7091

ENV NETUID=$NETUID
ENV WALLET_NAME=$WALLET_NAME
ENV WALLET_HOTKEY=$WALLET_HOTKEY
ENV WALLET_PATH=$WALLET_PATH
ENV SUBTENSOR_NETWORK=$SUBTENSOR_NETWORK
ENV SUBTENSOR_CHAIN_ENDPOINT=$SUBTENSOR_CHAIN_ENDPOINT
ENV SUBTENSOR_NODE_ID=$SUBTENSOR_NODE_ID
ENV AXON_PORT=$AXON_PORT

# Set the command to run your Python application
ENTRYPOINT ["./entrypoint.sh"]