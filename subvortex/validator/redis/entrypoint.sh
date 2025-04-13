#!/bin/sh

# Start Redis with the password provided via REDIS_PASSWORD environment variable
exec redis-server --requirepass "$SUBVORTEX_REDIS_PASSWORD"