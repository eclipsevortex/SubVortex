# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import os
import subprocess
from redis import asyncio as aioredis

from subvortex.core.shared.checks import *


async def check_redis_connection(port, redis_conf_path: str = "/etc/redis/redis.conf"):
    redis_password = _get_redis_password(redis_conf_path)

    # When coming from redis.conf no password is an empty string
    if redis_password == "":
        redis_password = None

    assert port is not None, "Redis server port not found"
    try:
        client = aioredis.StrictRedis(
            port=port, db=0, password=redis_password, socket_connect_timeout=1
        )
        await client.ping()
    except Exception as e:
        assert False, f"Redis connection failed. ConnectionError'{e}'"


def _get_redis_password(redis_conf_path):
    try:
        # Check environment variable first
        redis_password = os.getenv("SUBVORTEX_DATABASE_PASSWORD")
        if redis_password:
            return redis_password

        if not redis_conf_path or not os.path.exists(redis_conf_path):
            return None

        # Try to extract requirepass from the config
        cmd = f"sudo grep -Po '^requirepass \\K.*' {redis_conf_path}"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)

        # If grep didn't find anything, return None
        if result.returncode != 0 or not result.stdout.strip():
            return None

        return result.stdout.strip()

    except Exception as e:
        assert False, f"An unexpected error occurred: {e}"

    return None
