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
import json
import shutil
import bittensor as bt


def load_request_log(request_log_path: str) -> dict:
    """
    Loads the request logger from disk if it exists.

    Args:
        log_path (str): The path to the directory containing the request log.

    Returns:
        Dict: The request log data, if it exists, or an empty dictionary.

    This method loads the request log from disk if it exists. If not, it returns an empty dictionary.
    """
    if os.path.exists(request_log_path):
        try:
            with open(request_log_path, "r") as f:
                request_log = json.load(f)
        except Exception as e:
            bt.logging.error(f"Error loading request log: {e}. Resetting.")
            request_log = {}
    else:
        request_log = {}
    return request_log


def get_disk_space_stats(path):
    """
    Retrieves the disk space statistics for the drive containing the specified path.

    This function provides the total, used, and free disk space of the drive on which the specified path resides.
    It's useful for understanding the storage capacity and usage of the system where the miner is running.

    Args:
        path (str): A file path on the drive whose disk space statistics are to be fetched. Typically, you can
                    provide the root path ('/') to get the stats for the primary drive.

    Returns:
        dict: A dictionary containing the 'total_gb', 'used_gb', and 'free_gb', representing the total, used,
              and free space on the disk in gigabytes (GB), respectively.

    Usage:
        disk_stats = get_disk_space_stats('/')
    """
    path = os.path.expanduser(path)
    total, used, free = shutil.disk_usage(path)
    return {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
    }


def get_free_disk_space(path="."):
    """
    Retrieves the free disk space for the drive containing the specified path.

    This function provides the free disk space of the drive on which the specified path resides.
    It's useful for understanding the storage capacity and usage of the system where the miner is running.

    Args:
        path (str): A file path on the drive whose free disk space is to be fetched. Typically, you can
                    provide the root path ('/') to get the stats for the primary drive.

    Returns:
        int: The free space on the disk in bytes (B).

    Usage:
        free_disk_space_gb = get_free_disk_space('/')
    """
    stats = get_disk_space_stats(path)
    free = stats.get("free_bytes", 0)
    return free


def get_directory_size(path):
    """
    Calculates the total size of files in a specified directory.

    This function traverses the directory at the given path, including all subdirectories, and sums up the size
    of each file to calculate the total directory size.

    Args:
        path (str): The file path of the directory whose size is to be calculated.

    Returns:
        int: The total size of the directory in bytes (B).

    Usage:
        directory_size_gb = get_directory_size('/path/to/directory')
    """
    total_size = 0
    path = os.path.expanduser(path)
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


def get_external_ip(config):
    if config.miner.local:
        try:
            process = os.popen("ifconfig eth0 | grep 'inet ' | awk '{print $2}' | tr -d '\n'")
            external_ip = process.readline()
            process.close()
            assert isinstance(bt.utils.networking.ip_to_int(external_ip), int)
            return str(external_ip)
        except Exception:
            pass

    return bt.utils.networking.get_external_ip()