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
import glob
import site
import shutil
import subprocess
import bittensor.utils.btlogging as btul
from os import path

here = path.abspath(path.dirname(__file__))


class Interpreter:
    def __init__(self):
        pass

    def remove_egg_directory(self):
        # Use glob to find directories ending with .egg-info
        egg_info_dirs = glob.glob(os.path.join(here, "../../*.egg-info"))

        # Remove any err-info directory
        for dir_path in egg_info_dirs:
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)

    def remove_egg_link(self):
        site_packages_dirs = site.getsitepackages()

        for dir_path in site_packages_dirs:
            if os.path.exists(dir_path):
                for file_name in os.listdir(dir_path):
                    if file_name.endswith(".egg-link"):
                        egg_link_path = os.path.join(dir_path, file_name)
                        os.remove(egg_link_path)

    def install_dependencies(self):
        self.remove_egg_directory()
        self.remove_egg_link()
        btul.logging.info(f"Artifacts removed successfully")

        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        btul.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        btul.logging.info(f"Source installed successfully")

    def upgrade_dependencies(self):
        subprocess.run(["pip", "install", "--upgrade", "SubVortex"])
        btul.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        btul.logging.info(f"Source installed successfully")
