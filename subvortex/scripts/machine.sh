#!/bin/bash

#
# Check the system of the machine
#
function get_os()
{
    if [[ $(uname) == "Darwin" ]]; then
        echo "macos"
    elif [[ -f /etc/lsb-release && $(grep -c "Ubuntu" /etc/lsb-release) -gt 0 ]]; then
        echo "linux"
    elif [[ -f /etc/os-release && $(grep -c "NAME=\"Ubuntu\"" /etc/os-release) -eq 0 ]]; then
        echo "linux"
    else
        echo "Unknown"
    fi
}
