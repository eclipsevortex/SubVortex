# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Rust using rustup
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Add Cargo in path
ENV PATH="/root/.cargo/bin:${PATH}"

# Install the dependencies
COPY ./miner/neuron/requirements.txt ./miner/neuron/
RUN pip install --upgrade pip && pip install -r ./miner/neuron/requirements.txt --no-cache-dir

# Copy files
COPY ./core/neuron ./core/neuron
COPY ./core/tdbittensor ./core/tdbittensor
COPY ./core/proxy ./core/proxy
COPY ./miner/neuron/src ./miner/neuron/src
COPY ./miner/neuron/pyproject.toml ./miner/neuron
COPY ./miner/neuron/entrypoint.sh ./miner/neuron/entrypoint.sh

WORKDIR /app/miner/neuron

# Install the dependencies
RUN pip install -e .

# Specify the command to run your application
ENTRYPOINT ["./entrypoint.sh"]