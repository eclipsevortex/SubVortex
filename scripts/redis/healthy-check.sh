#!/bin/bash

password=$(sudo grep -Po '^requirepass \K.*' /etc/redis/redis.conf)

while true; do
    output=$(redis-cli -a $password ping 2>/dev/null)
    if [[ $output == "Could not connect to Redis"* ]]; then
        systemctl restart redis-server
    else 
        echo $output
    fi

    sleep 1
done