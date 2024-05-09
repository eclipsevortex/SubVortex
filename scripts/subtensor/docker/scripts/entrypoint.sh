#!/bin/bash

# Define the command with common arguments
command="./target/release/node-subtensor --base-path /tmp/alice --chain="$CHAIN_SPEC" --alice --port 30334 --rpc-port 9946 --validator --rpc-cors all --allow-private-ipv4 --discover-local --unsafe-ws-external"

# Execute the command
exec $command &

sleep 5

command="./target/release/node-subtensor --base-path /tmp/bob --chain="$CHAIN_SPEC" --bob --port 30335 --rpc-port 9945 --validator --allow-private-ipv4 --discover-local"

exec $command &

wait 

