#!/usr/bin/env bash

#
# Helper functions
#

function run_command()
{
    F_NETWORK=$1
    F_NODE_TYPE=$2
    F_BIN_PATH=$3
    
    # Different command options by network and node type
    MAINNET_CHAIN='--chain ./raw_spec_finney.json'
    TESTNET_CHAIN='--chain ./raw_spec_testfinney.json'
    MAINNET_BOOTNODE='--bootnodes /ip4/13.58.175.193/tcp/30333/p2p/12D3KooWDe7g2JbNETiKypcKT1KsCEZJbTzEHCn8hpd4PHZ6pdz5'
    # MAINNET_BOOTNODE='--bootnodes /dns/bootnode.finney.opentensor.ai/tcp/30333/ws/p2p/12D3KooWRwbMb85RWnT8DSXSYMWQtuDwh4LJzndoRrTDotTR5gDC'
    TESTNET_BOOTNODE='--bootnodes /dns/bootnode.test.finney.opentensor.ai/tcp/30333/p2p/12D3KooWPM4mLcKJGtyVtkggqdG84zWrd7Rij6PGQDoijh1X86Vr'
    NODE_TYPE_ARCHIVE='--pruning=archive'
    NODE_TYPE_LITE='--sync warp'
    
    
    # Options by the type of node we offer
    MAINNET_ARCHIVE_OPTIONS="$MAINNET_CHAIN $MAINNET_BOOTNODE $NODE_TYPE_ARCHIVE"
    MAINNET_LITE_OPTIONS="$MAINNET_CHAIN $MAINNET_BOOTNODE $NODE_TYPE_LITE"
    TESTNET_ARCHIVE_OPTIONS="$TESTNET_CHAIN $TESTNET_BOOTNODE $NODE_TYPE_ARCHIVE"
    TESTNET_LITE_OPTIONS="$TESTNET_CHAIN $TESTNET_BOOTNODE $NODE_TYPE_LITE"
    
    # Checking options to use
    if [[ "$F_NETWORK" == "mainnet" ]] && [[ "$F_NODE_TYPE" == "archive" ]]; then
        SPECIFIC_OPTIONS=$MAINNET_ARCHIVE_OPTIONS
        elif [[ "$F_NETWORK" == "mainnet" ]] && [[ "$F_NODE_TYPE" == "lite" ]]; then
        SPECIFIC_OPTIONS=$MAINNET_LITE_OPTIONS
        elif [[ "$F_NETWORK" == "testnet" ]] && [[ "$F_NODE_TYPE" == "archive" ]]; then
        SPECIFIC_OPTIONS=$TESTNET_ARCHIVE_OPTIONS
        elif [[ "$F_NETWORK" == "testnet" ]] && [[ "$F_NODE_TYPE" == "lite" ]]; then
        SPECIFIC_OPTIONS=$TESTNET_LITE_OPTIONS
    fi
    
    if [ ! -f $F_BIN_PATH ]; then
        echo "Binary '$F_BIN_PATH' does not exist. You can use -p or --bin-path to specify a different location."
        echo "Please ensure you have compiled the binary first."
        exit 1
    fi
    
    # Command to run subtensor
    $F_BIN_PATH \
    --base-path /tmp/blockchain \
    --execution wasm \
    --wasm-execution compiled \
    --port 30333 \
    --max-runtime-instances 32 \
    --rpc-max-response-size 2048 \
    --rpc-cors all \
    --rpc-port 9944 \
    --no-mdns \
    --in-peers 8000 \
    --out-peers 8000 \
    --prometheus-external \
    --rpc-external \
    $SPECIFIC_OPTIONS
}


# Default values
EXEC_TYPE="docker"
NETWORK="mainnet"
NODE_TYPE="lite"
BUILD=""
BIN_PATH="./target/release/node-subtensor"

# Getting arguments from user
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            help
            exit 0
        ;;
        -e|--execution)
            EXEC_TYPE="$2"
            shift # past argument
            shift # past value
        ;;
        -b|--build)
            BUILD="--build"
            shift # past argument
        ;;
        -n|--network)
            NETWORK="$2"
            shift
            shift
        ;;
        -t|--node-type)
            NODE_TYPE="$2"
            shift
            shift
        ;;
        -p|--bin-path)
            BIN_PATH="$2"
            shift
            shift
        ;;
        -*|--*)
            echo "Unknown option $1"
            exit 1
        ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
        ;;
    esac
done

# Verifying arguments values
if ! [[ "$EXEC_TYPE" =~ ^(docker|binary)$ ]]; then
    echo "Exec type not expected: $EXEC_TYPE"
    exit 1
fi

if ! [[ "$NETWORK" =~ ^(mainnet|testnet)$ ]]; then
    echo "Network not expected: $NETWORK"
    exit 1
fi

if ! [[ "$NODE_TYPE" =~ ^(lite|archive)$ ]]; then
    echo "Node type not expected: $NODE_TYPE"
    exit 1
fi

# Running subtensor
case $EXEC_TYPE in
    docker)
        cd $HOME/subtensor
        docker compose down --remove-orphans
        echo "Running docker compose up $BUILD --detach $NETWORK-$NODE_TYPE"
        docker compose up $BUILD --detach $NETWORK-$NODE_TYPE
    ;;
    binary)
        run_command $NETWORK $NODE_TYPE $BIN_PATH
    ;;
esac
