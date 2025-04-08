ARG SUBVORTEX_OBSERVER_TYPE=file

# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Re-declare the ARG after FROM if you want to use it in this stage
ARG SUBVORTEX_OBSERVER_TYPE=file

# Set the env var
ENV SV_OBSERVER_TYPE=${SUBVORTEX_OBSERVER_TYPE}

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
COPY ./neuron/requirements.txt ./neuron/
RUN pip install --upgrade pip && pip install -r ./neuron/requirements.txt --no-cache-dir

# Copy files
COPY ./core/utils ./core/utils
COPY ./neuron/src ./neuron/src
COPY ./neuron/pyproject.toml ./neuron
COPY ./neuron/entrypoint.sh ./neuron/entrypoint.sh

WORKDIR /app/neuron

# Install the observer dependencies
RUN pip install ".[observer-${SV_OBSERVER_TYPE}]"

# Install the dependencies
RUN pip install -e .

# Specify the command to run your application
ENTRYPOINT ["./entrypoint.sh"]