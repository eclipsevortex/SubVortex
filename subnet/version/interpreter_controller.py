import subprocess
import bittensor as bt


class Interpreter:
    def __init__(self):
        pass

    def install_dependencies(self):
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        bt.logging.info(f"Dependencies installed successfully")

        subprocess.run(["pip", "install", "-e", "."])
        bt.logging.info(f"Source installed successfully")

    def upgrade_dependencies(self):
        subprocess.run(["pip", "install", "-r", "requirements.txt", "--upgrade"])
        bt.logging.info(f"Dependencies installed successfully")
