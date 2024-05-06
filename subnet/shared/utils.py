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
import time
import subprocess
import bittensor as bt


def get_redis_password(
    redis_password: str = None, redis_conf: str = "/etc/redis/redis.conf"
) -> str:
    redis_password = os.getenv("REDIS_PASSWORD") or redis_password
    if redis_password is None:
        try:
            redis_password = subprocess.check_output(
                ["sudo", "grep", "-Po", "^requirepass \K.*", redis_conf],
                text=True,
            ).strip()
        except Exception as e:
            bt.logging.error(
                f"No Redis password set in Redis config file: {redis_conf}"
            )
    if redis_password == "" or redis_password is None:
        bt.logging.error(
            "Redis password not found! This must be set as either an env var `REDIS_PASSWORD`, passed via CLI in `--database.redis_pasword`, or parsed from /etc/redis/redis.conf."
            "Please ensure it is set by running `. ./scripts/redis/set_redis_password.sh` and try again."
            f"You may also run: `sudo grep -Po '^requirepass \K.*' {redis_conf}` to discover this manually and pass to the cli."
        )
        exit(1)

    return redis_password


def should_upgrade(auto_update: bool, last_upgrade_check: float):
    """
    True if it is sime to upgrade, false otherwise
    For now, upgrading evering 60 seconds
    """
    time_since_last_update = time.time() - last_upgrade_check
    return time_since_last_update >= 60 and auto_update
