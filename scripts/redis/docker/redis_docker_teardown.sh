#!/bin/bash

# Stop redis container
docker-compose stop redis
echo -e "\\033[32mRedis stopped\\033[0m"

# Remove redis container and everything related
docker-compose down &> /dev/null
echo -e "\\033[32mRedis cleaned\\033[0m"

# Down and remove volumes
docker-compose down --volumes &> /dev/null
echo -e "\\033[32mVolumes removed\\033[0m"

# Remove redis container and everything related
docker-compose down --rmi all &> /dev/null
echo -e "\\033[32mImages removed\\033[0m"