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

convert_env_var_to_args() {
    PREFIX="SUBVORTEX_"
    local args=()

    while IFS= read -r line; do
        key="${line%%=*}"
        value="${line#*=}"

        # Skip if key doesn't start with PREFIX or value is empty (even if it's just "")
        if [[ $key != ${PREFIX}* || -z "${value//\"/}" ]]; then
            continue
        fi

        key_suffix="${key#$PREFIX}"
        cli_key="--$(echo "$key_suffix" | tr '[:upper:]' '[:lower:]' | tr '_' '.')"
        value_lower="$(echo "$value" | tr '[:upper:]' '[:lower:]')"

        if [[ "$value_lower" == "true" ]]; then
            args+=("$cli_key")
        elif [[ "$value_lower" == "false" ]]; then
            continue
        else
            args+=("$cli_key" "$value")
        fi
    done < <(env)

    # Output escaped values so caller can eval safely
    printf '%q ' "${args[@]}"
}