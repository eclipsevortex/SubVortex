#!/bin/bash

# Stop container
docker-compose down
echo -e "\\033[32mServices cleaned\\033[0m"

# Down and remove volumes
docker-compose down --volumes &> /dev/null
echo -e "\\033[32mVolumes removed\\033[0m"

# Remove subtensor container and everything related
docker-compose down --rmi all &> /dev/null
echo -e "\\033[32mImages removed\\033[0m"

# Remove unused container
docker container prune -f

# Remove unused container
docker image prune -f

# Remove unused volume
docker volume prune -f

# Remove unused network
docker network prune -f