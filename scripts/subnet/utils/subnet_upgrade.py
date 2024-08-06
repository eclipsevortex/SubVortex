import asyncio
import argparse
import subprocess
import bittensor as bt

from subnet.miner.version import VersionControl as MinerVersionControl
from subnet.validator.version import VersionControl as ValidatorVersionControl


def get_current_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_current_tag():
    result = subprocess.run(
        ["git", "--tags", "--exact-match"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_current_branch_or_tag():
    try:
        tag = get_current_tag()
        return ("tag", tag)
    except subprocess.CalledProcessError:
        branch = get_current_branch()
        return ("branch", branch)


def get_tags():
    subprocess.run(["git", "fetch", "--tags", "--force"], check=True)
    bt.logging.info(f"Fetch tags.")


def upgrade_to_tag(tag: str):
    # Get current branch or tag
    _, tag_or_branch = get_current_branch_or_tag()

    # Check if the requested tag is already pulled
    if tag_or_branch == tag:
        bt.logging.warning(f"The tag {tag} is already pulled")
        return

    # Stash if there is any local changes just in case
    subprocess.run(["git", "stash"], check=True)

    # Fetch all tags
    subprocess.run(["git", "fetch", "--tags", "--force"], check=True)
    bt.logging.debug(f"Fetch tags")

    # Pull the requested tag
    subprocess.run(["git", "checkout", f"tags/{tag}"], check=True)
    bt.logging.success(f"Successfully pulled source code for tag '{tag}'.")


def upgrade_to_branch(branch: str):
    # Get current branch or tag
    _, tag_or_branch = get_current_branch_or_tag()

    # Check if the requested tag is already pulled
    if tag_or_branch == branch:
        bt.logging.warning(f"The branch {branch} is already pulled")
        return

    # Stash if there is any local changes just in case
    subprocess.run(["git", "stash"], check=True)

    # Checkout the branch
    subprocess.run(["git", "checkout", "-B", branch], check=True)
    bt.logging.debug(f"Checkout the branch {branch}")

    # Pull the branch
    subprocess.run(["git", "pull", "origin", branch], check=True)
    bt.logging.debug(f"Pull the branch {branch}")

    bt.logging.success(f"Successfully pulled source code for {branch} branch'.")


def main(args):
    if not args.tag and not args.branch:
        bt.logging.error(f"Please provide a tag or a branch to upgrade to")
        return
    
    version_control = MinerVersionControl()
    version_control.upgrade(tag=args.tag, branch=args.branch)

    # if args.miner:
    #     version_control = MinerVersionControl()
    #     version_control.upgrade(tag=args.tag, branch=args.branch)
    # else:
    #     version_control = ValidatorVersionControl()
    #     version_control.upgrade(tag=args.tag, branch=args.branch)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--tag", type=str, help="Tag to pull", default=None)
        parser.add_argument("--branch", type=str, help="Branch to pull", default=None)
        parser.add_argument(
            "--miner",
            action="store_true",
            help="True if miner upgrade, False if validator",
            default=False,
        )
        args = parser.parse_args()

        main(args)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ValueError as e:
        print(f"ValueError: {e}")
