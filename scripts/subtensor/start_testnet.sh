cd ~/subtensor/
pm2 start ./target/release/node-subtensor \
    --name test_subtensor -- \
    --base-path /tmp/blockchain \
    --chain ./raw_testspec.json \
    --rpc-external --rpc-cors all \
    --ws-external --no-mdns \
    --ws-max-connections 10000 --in-peers 500 --out-peers 500 \
    --bootnodes /ip4/75.119.138.170/tcp/30333/ws/p2p/12D3KooWPrWvB2ZQ8Rn71uyPk9gZFTi7mqhkabka3ZkCXx7gaEBs \
    --sync warp
