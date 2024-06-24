import os
import glob
import shutil
from os import path
import subprocess
import bittensor as bt

here = path.abspath(path.dirname(__file__))


class Interpreter:
    def __init__(self):
        pass

    def install_dependencies(self):
        # Use glob to find directories ending with .egg-info
        egg_info_dirs = glob.glob(os.path.join(here, "../../*.egg-info"))

        # Remove any err-info directory
        for dir_path in egg_info_dirs:
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
        bt.logging.info(f"Metadata removed successfully")

        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        bt.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        bt.logging.info(f"Source installed successfully")

    def upgrade_dependencies(self):
        subprocess.run(["pip", "install", "--upgrade", "SubVortex"])
        bt.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        bt.logging.info(f"Source installed successfully")
