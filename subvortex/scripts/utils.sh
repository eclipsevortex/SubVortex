#!/bin/bash

set -e

# Define the function
get_tag() {
    local enabled="${SUBVORTEX_PRERELEASE_ENABLED:-}"
    local type="${SUBVORTEX_PRERELEASE_TYPE:-}"
    
    if [[ "$enabled" = "False" || "$enabled" = "false" ]]; then
        echo "latest"
        elif [ "$type" = "alpha" ]; then
        echo "dev"
        elif [ "$type" = "rc" ]; then
        echo "stable"
    else
        echo "latest"
    fi
}

check_required_args() {
    local missing=()
    for var in "$@"; do
        if [ -z "${!var}" ]; then
            missing+=("$var")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "❌ Missing required argument(s):"
        for var in "${missing[@]}"; do
            local flag_name
            flag_name=$(echo "$var" | tr '[:upper:]' '[:lower:]')
            echo "   --$flag_name <value>  (env var: $var)"
        done
        
        echo -n "👉 Example: $0 "
        for var in "${missing[@]}"; do
            flag_name=$(echo "$var" | tr '[:upper:]' '[:lower:]')
            printf -- '--%s <value> ' "$flag_name"
        done
        echo
        exit 1
    fi
}

