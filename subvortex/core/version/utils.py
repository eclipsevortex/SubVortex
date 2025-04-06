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
import re
import shutil
import importlib
import bittensor.utils.btlogging as btul
from os import path

here = path.abspath(path.dirname(__file__))


def extract_number(s):
    """
    Extract the numbers (major, minor and patch) from the string version
    """
    try:
        match = re.search(r"(\d+)\.(\d+)\.(\d+)\.py", s)
        if not match:
            return None

        patch = int(match.group(3))
        minor = int(match.group(2))
        major = int(match.group(1))
        return (major, minor, patch)
    except Exception as ex:
        btul.logging.error(f"Could not extract the numbers from the string version: {ex}")

    return None


def get_migrations(force_new=False, reverse=False, filter_lambda = None):
    """
    List all the migrations available
    """
    migrations = []

    try:
        source = os.path.join(here, "../../scripts/redis/previous_migrations")
        if force_new or not os.path.exists(source):
            source = os.path.join(here, "../../scripts/redis/migrations")

        # Load the migration scripts
        files = os.listdir(source)

        # Get all the migration files
        for file in files:
            if not re.match(r"migration-[0-9]+\.[0-9]+\.[0-9]+.py", file):
                continue

            version_details = extract_number(file)
            if not version_details:
                continue

            major, minor, patch = version_details
            migrations.append(
                (int(f"{major}{minor}{patch}"), f"{major}.{minor}.{patch}", file)
            )

        # Filter the migrations
        if filter_lambda:
            migrations = filter(filter_lambda, migrations)

        # Sort migration per version
        migrations = sorted(migrations, key=lambda x: x[0], reverse=reverse)

    except Exception as ex:
        btul.logging.error(f"Could not load the migrations: {ex}")

    return migrations


def create_dump_migrations():
    """
    Create a migrations dump
    """
    source = os.path.join(here, "../../scripts/redis/migrations")
    if not os.path.exists(source):
        return

    target = os.path.join(here, "../../scripts/redis/previous_migrations")
    if os.path.exists(target):
        shutil.rmtree(target)

    # Dump the migrations directory
    shutil.copytree(source, target)


def remove_dump_migrations():
    """
    Remove the migrations dump
    """
    target = os.path.join(here, "../../scripts/redis/previous_migrations")
    if not os.path.exists(target):
        return

    shutil.rmtree(target)


def get_migration_module(migration: str):
    file_path = f"scripts/redis/previous_migrations/{migration}"
    if not os.path.exists(file_path):
        file_path = f"scripts/redis/migrations/{migration}"

    spec = importlib.util.spec_from_file_location("migration_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
