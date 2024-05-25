#!/bin/bash

# Start Alice node
command="./target/release/node-subtensor --base-path /tmp/alice --chain "$CHAIN_SPEC" --alice --port 30334 --rpc-port 9946 --rpc-cors all --allow-private-ipv4 --discover-local --ws-port 9944 --unsafe-ws-external"
exec $command &

sleep 5

# Start bob node
command="./target/release/node-subtensor --base-path /tmp/bob --chain "$CHAIN_SPEC" --bob --port 30335 --rpc-port 9945 --allow-private-ipv4 --discover-local"
exec $command &

sleep 5

wait

