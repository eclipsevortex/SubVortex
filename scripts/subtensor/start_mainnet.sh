cd ~/subtensor/
pm2 start ./target/release/node-subtensor \
    --name subtensor -- \
    --base-path /tmp/blockchain \
    --chain ./raw_spec.json \
    --rpc-external --rpc-cors all \
    --ws-external --no-mdns \
    --ws-max-connections 10000 --in-peers 500 --out-peers 500 \
    --bootnodes /dns/bootnode.finney.opentensor.ai/tcp/30333/ws/p2p/12D3KooWRwbMb85RWnT8DSXSYMWQtuDwh4LJzndoRrTDotTR5gDC \
    --sync warp
