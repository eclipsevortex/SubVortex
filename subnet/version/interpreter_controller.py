import os
import glob
import site
import shutil
from os import path
import subprocess
import bittensor as bt

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
        bt.logging.info(f"Artifacts removed successfully")

        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        bt.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        bt.logging.info(f"Source installed successfully")

    def upgrade_dependencies(self):
        subprocess.run(["pip", "install", "--upgrade", "SubVortex"])
        bt.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        bt.logging.info(f"Source installed successfully")
