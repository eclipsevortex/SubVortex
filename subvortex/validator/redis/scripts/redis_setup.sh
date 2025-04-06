#!/bin/bash

set -e

# Help function
show_help() {
    echo "Usage: $0 [--execution=process|container|service]"
    echo
    echo "Options:"
    echo "  --execution   Specify the execution method (default: service)"
    echo "  --help        Show this help message"
    exit 0
}

OPTIONS="e:h"
LONGOPTIONS="execution:,help:"

# Parse the options and their arguments
params="$(getopt -o $OPTIONS -l $LONGOPTIONS: --name "$0" -- "$@")"

# Check for getopt errors
if [ $? -ne 0 ]; then
    exit 1
fi

METHOD=service

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -e |--execution)
            METHOD="$2"
            shift 2
        ;;
        -h | --help)
            show_help
            exit 0
        ;;
        *)
            echo "Unrecognized option '$1'"
            exit 1
        ;;
    esac
done

# Load environment variables
export $(grep -v '^#' ./subvortex/validator/redis/.env | xargs)

# Install if needed docker if the auto uprader is managing the upgrade of containers
if [[ "$SUBVORTEX_EXECUTION_METHOD" == "container" ]]; then
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Installing it now."
        ./scripts/docker/docker_setup.sh
    fi
fi

# 🧠 Function: Setup for process mode
setup_process() {
    echo "⚙️  Setting up for 'process' mode..."
    
    # Install pm2
    ./scripts/install_pm2.sh
    
    # Setup the auto upgrade as process
    ./subvortex/validator/redis/deployment/process/redis_process_setup.sh
    
    # Add any other logic specific to process mode here
    echo "✅ Process setup complete."
}

# 🐳 Function: Setup for container mode
setup_container() {
    echo "🐳 Setting up for 'container' mode..."
    
    # Setup the auto upgrade as container
    ./subvortex/validator/redis/deployment/docker/redis_docker_setup.sh
    
    # Add any other container-specific logic here
    echo "✅ Container setup complete."
}

# 🧩 Function: Setup for service mode
setup_service() {
    echo "🧩 Setting up for 'service' mode..."
    
    # Setup the auto upgrade as service
    ./subvortex/validator/redis/deployment/service/redis_service_setup.sh
    
    # Add logic for systemd, service checks, etc. if needed
    echo "✅ Service setup complete."
}

# 🚀 Function: Dispatch based on method
run_setup() {
    # Install Auto Upgrade
    case "$METHOD" in
        process)
            setup_process
        ;;
        container)
            setup_container
        ;;
        service)
            setup_service
        ;;
        *)
            echo "❌ Unknown METHOD: '$METHOD'"
            exit 1
        ;;
    esac
}

# 🔥 Execute
run_setup
