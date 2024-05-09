FROM ubuntu:22.04

SHELL ["/bin/bash", "-c"]

# Install git and other dependencies
RUN apt-get update && \
  apt-get install -y curl build-essential protobuf-compiler clang git && \
  rm -rf /var/lib/apt/lists/*

# Clone the Git repository into the container
RUN git clone https://github.com/opentensor/subtensor.git

WORKDIR /subtensor

# Checkout main branch
RUN git checkout main

# Pull the main branch
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

COPY ./scripts/subtensor/docker/scripts/entrypoint.sh .

EXPOSE 30334 30335 9945 9946 9944

# Run the program
ENTRYPOINT ["/subtensor/entrypoint.sh"]