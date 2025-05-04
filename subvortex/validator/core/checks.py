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
import asyncio
import subprocess
from redis import asyncio as aioredis

from subvortex.core.shared.checks import *


async def check_environment(redis_conf_path: str = "/etc/redis/redis.conf"):
    redis_port = 6379
    _check_redis_config(redis_conf_path)
    _check_redis_settings(redis_conf_path)
    _assert_setting_exists(redis_conf_path, "requirepass")
    await check_redis_connection(redis_conf_path, redis_port)
    await _check_data_persistence(redis_conf_path, redis_port)


def _check_redis_config(path):
    try:
        subprocess.run(["sudo", "test", "-f", path], check=True)
    except subprocess.CalledProcessError:
        raise AssertionError(f"Redis config file path: '{path}' does not exist.")


def _check_redis_settings(redis_conf_path):
    settings_to_check = [
        ("appendonly", ["appendonly yes"]),
        ("save", ["save 900 1", "save 300 10", "save 60 10000"]),
    ]

    for setting, expected_values in settings_to_check:
        _check_redis_setting(redis_conf_path, setting, expected_values)


async def check_redis_connection(port, redis_conf_path: str = "/etc/redis/redis.conf"):
    redis_password = _get_redis_password(redis_conf_path)

    assert port is not None, "Redis server port not found"
    try:
        client = aioredis.StrictRedis(
            port=port, db=0, password=redis_password, socket_connect_timeout=1
        )
        await client.ping()
    except Exception as e:
        assert False, f"Redis connection failed. ConnectionError'{e}'"


async def _check_data_persistence(redis_conf_path, port):
    redis_password = _get_redis_password(redis_conf_path)

    assert port is not None, "Redis server port not found"
    client = aioredis.StrictRedis(port=port, db=0, password=redis_password)

    # Insert data into Redis
    await client.set("testkey", "Hello, Redis!")

    # Restart Redis server
    subprocess.run(["sudo", "systemctl", "restart", "redis-server"], check=True)

    # Wait a bit to ensure Redis has restarted
    await asyncio.sleep(5)

    # Reconnect to Redis
    assert port is not None, "Redis server port not found after restart"
    new_redis = aioredis.StrictRedis(port=port, db=0, password=redis_password)

    # Retrieve data from Redis
    value = await new_redis.get("testkey")
    assert port is not None, "The key testkey is not there"

    # Restart Redis server
    subprocess.run(["sudo", "systemctl", "restart", "redis-server"], check=True)

    # Wait a bit to ensure Redis has restarted
    await asyncio.sleep(5)

    # Reconnect to Redis
    assert port is not None, "Redis server port not found after restart"
    new_redis = aioredis.StrictRedis(port=port, db=0, password=redis_password)

    # Remove data
    await new_redis.delete("testkey")

    # Restart Redis server
    subprocess.run(["sudo", "systemctl", "restart", "redis-server"], check=True)

    # Wait a bit to ensure Redis has restarted
    await asyncio.sleep(5)

    # Reconnect to Redis
    assert port is not None, "Redis server port not found after restart"
    new_redis = aioredis.StrictRedis(port=port, db=0, password=redis_password)

    # Retrieve data from Redis
    value = await new_redis.get("testkey")
    assert port is None, "The key testkey is still there"

    await new_redis.aclose()
    del new_redis

    # Check if the value is what we expect
    assert (
        value.decode("utf-8") == "Hello, Redis!"
    ), "Data did not persist across restart."


def _check_redis_setting(file_path, setting, expected_values):
    """Check if Redis configuration contains all expected values for a given setting."""
    actual_values = _assert_setting_exists(file_path, setting)
    assert sorted(actual_values) == sorted(
        expected_values
    ), f"Configuration for '{setting}' does not match expected values. Got '{actual_values}', expected '{expected_values}'"


def _assert_setting_exists(file_path, setting):
    actual_values = _get_redis_setting(file_path, setting)
    assert actual_values is not None, f"Redis config missing setting '{setting}'"
    return actual_values


def _get_redis_setting(file_path, setting):
    """Retrieve specific settings from the Redis configuration file."""
    try:
        result = subprocess.check_output(
            ["sudo", "grep", f"^{setting}", file_path], text=True
        )
        return result.strip().split("\n")
    except subprocess.CalledProcessError:
        return None


def _get_redis_password(redis_conf_path):
    try:
        redis_password = os.getenv("SUBVORTEX_DATABASE_PASSWORD")
        if redis_password:
            return redis_password

        if not redis_conf_path:
            return None

        if not os.path.exists(redis_conf_path):
            return None

        cmd = f"sudo grep -Po '^requirepass \K.*' {redis_conf_path}"
        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        assert False, f"Command failed: {e}"
    except Exception as e:
        assert False, f"An error occurred: {e}"

    return None
