#!/bin/bash

# Create log files
touch /var/log/alice.log /var/log/bob.log /var/log/miner.log

# Subtensor
## Alice node - use the bootnode from the subvortex-subnet
cd subtensor && ./target/release/node-subtensor \
--base-path /tmp/alice \
--chain="raw_localspec.json" \
--alice \
--port 30334 \
--rpc-port 9946 \
--validator \
--rpc-cors all \
--allow-private-ipv4 \
--discover-local \
--ws-port 9944 \
--unsafe-ws-external \
--bootnodes $SUBTENSOR_NODE_ID \
> /var/log/alice.log 2>&1 &

## Bob node - use the bootnode from the subvortex-subnet
cd subtensor && ./target/release/node-subtensor \
--base-path /tmp/bob \
--chain="raw_localspec.json" \
--bob \
--port 30335 \
--rpc-port 9945 \
--ws-port 9943 \
--validator \
--allow-private-ipv4 \
--discover-local \
> /var/log/bob.log 2>&1 &

# Sleep to let time for the subtensor to be sync
sleep 5

# Miner
cd SubVortex && ./entrypoint.sh > /var/log/miner.log 2>&1 &

# Tail the log files to stdout to capture them in docker logs
tail -f /var/log/miner.log &
 
# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
