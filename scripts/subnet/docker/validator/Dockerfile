FROM python:3.10 as builder

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy subnet source
COPY ./neurons /SubVortex/neurons
COPY ./subnet /SubVortex/subnet
COPY ./setup.py /SubVortex
COPY ./requirements.txt /SubVortex
COPY ./VERSION /SubVortex
COPY ./README.md /SubVortex


FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy SubVortex source code
COPY --from=builder /SubVortex /app/SubVortex

# Go to SubVortex directory
WORKDIR /app/SubVortex

# Install project dependencies
RUN pip install -r requirements.txt

# Install the source
RUN pip install -e .

COPY ./scripts/subnet/docker/validator/entrypoint.sh .

# Define default values for arguments
ARG NETUID=1
ARG WALLET_NAME=validator-1
ARG WALLET_HOTKEY=validator-1-1
ARG WALLET_PATH=/.bittensor/wallets
ARG DABASE_INDEX=0
ARG SUBTENSOR_NETWORK
ARG SUBTENSOR_CHAIN_ENDPOINT=ws://subvortex-subnet:9944
ARG AXON_PORT=8091

ENV NETUID=$NETUID
ENV WALLET_NAME=$WALLET_NAME
ENV WALLET_HOTKEY=$WALLET_HOTKEY
ENV WALLET_PATH=$WALLET_PATH
ENV DABASE_INDEX=$DABASE_INDEX
ENV SUBTENSOR_NETWORK=$SUBTENSOR_NETWORK
ENV SUBTENSOR_CHAIN_ENDPOINT=$SUBTENSOR_CHAIN_ENDPOINT
ENV AXON_PORT=$AXON_PORT

# Set the command to run your Python application
ENTRYPOINT ["/app/SubVortex/entrypoint.sh"]