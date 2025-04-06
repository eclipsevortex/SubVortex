import re
import os
import toml
import asyncio
import requests
import argparse
import traceback
import subprocess
from packaging.version import Version

import bittensor.core.config as btcc
import bittensor.utils.btlogging as btul

import deployer.src.config as dc


class Worker:
    def __init__(self, config):
        self.config = dc.Config(config)

    def run(self):
        # Get the list of components for the target you want to deploy
        components = self._resolve_components(self.config.TARGETS)

        btul.logging.info(f"📦 Components to deploy: {components}")

        for component in components:
            try:
                # Build the name of the component
                component_name = self._read_name(component=component)

                # Get the current version
                current = self._read_version(component=component)
                btul.logging.debug(f"Current version: {current}", prefix=component_name)

                # Bump the base version
                new_version = self._bump_base_version(
                    version_str=current, bump_type=self.config.BUMP
                )

                # Get existing tags
                existing_tags = self._get_existing_tags()

                # Compute the new version
                if self.config.PRERELEASE:
                    new_version = self._bump_prerelease(
                        existing_tags=existing_tags,
                        base_version=new_version,
                        prefix=component,
                        prerelease_type=self.config.PRERELEASE,
                    )
                btul.logging.debug(f"New version: {new_version}", prefix=component_name)

                # Update the version file
                self._update_version_file(component=component, new_version=new_version)
                btul.logging.debug("Version updated", prefix=component_name)

                # Build the tag
                tag = f"v{component_name}-{new_version}"

                # Commit and push tag
                self._git_commit_and_tag(tag=tag, path=component)

                # Check if it is a prerelease or not
                prerelease = any(x in new_version for x in ["alpha", "rc"])

                # Create the release
                self._create_github_release(
                    tag=tag,
                    name=f"{component_name} {new_version}",
                    prerelease=prerelease,
                )

                # Build and push docker image
                self._build_and_push_docker_image(
                    path=component, component_name=component_name, version=new_version
                )

            except Exception as e:
                btul.logging.error(f"❌ Failed to bump {component}: {e}")
                continue

        btul.logging.success("🎉 Deploy complete!")

    def shutdown(self):
        pass

    def _bump_base_version(self, version_str: str, bump_type: str):
        version = Version(version_str)
        if bump_type == "patch":
            return f"{version.major}.{version.minor}.{version.micro + 1}"
        elif bump_type == "minor":
            return f"{version.major}.{version.minor + 1}.0"
        elif bump_type == "major":
            return f"{version.major + 1}.0.0"
        else:
            raise ValueError("Invalid bump type")

    def _bump_prerelease(self, existing_tags, base_version, prefix, prerelease_type):
        """
        Looks at tags like: vminer-1.2.4-alpha.1 and finds the highest -alpha.N for that base.
        """
        pattern = re.compile(
            rf"^v{prefix}-{re.escape(base_version)}-{prerelease_type}\.(\d+)$"
        )
        max_n = 0
        for tag in existing_tags:
            match = pattern.match(tag)
            if match:
                max_n = max(max_n, int(match.group(1)))
        return f"{base_version}-{prerelease_type}.{max_n + 1}"

    def _read_name(self, component: str):
        if os.path.exists(f"{component}/pyproject.toml"):
            data = toml.load(f"{component}/pyproject.toml")
            return data["project"]["name"]
        else:
            raise FileNotFoundError("No version file found")

    def _read_version(self, component: str):
        if os.path.exists(f"{component}/pyproject.toml"):
            data = toml.load(f"{component}/pyproject.toml")
            return data["project"]["version"]
        else:
            raise FileNotFoundError("No version file found")

    def _update_version_file(self, component: str, new_version: str):
        if self.config.DRY_RUN:
            return

        if os.path.exists(f"{component}/pyproject.toml"):
            data = toml.load(f"{component}/pyproject.toml")
            data["project"]["version"] = new_version
            with open(f"{component}/pyproject.toml", "w") as f:
                toml.dump(data, f)

    def _get_existing_tags(self):
        result = subprocess.run(["git", "tag"], capture_output=True, text=True)
        return result.stdout.strip().split("\n")

    def _git_commit_and_tag(self, tag, path):
        if self.config.DRY_RUN:
            return

        subprocess.run(["git", "add", path], check=True)
        subprocess.run(["git", "commit", "-m", f"release: {tag}"], check=True)
        subprocess.run(["git", "tag", tag], check=True)
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "origin", tag], check=True)

    def _build_and_push_docker_image(self, path, component_name, version):
        if self.config.DRY_RUN:
            return

        tag = f"{self.config.DOCKER_REPO}-{component_name}:v{version}"
        subprocess.run(["docker", "build", path, "-t", tag], check=True)
        subprocess.run(["docker", "push", tag], check=True)

    def _create_github_release(self, tag, name, prerelease):
        if self.config.DRY_RUN:
            return

        token = self.config.GITHUB_TOKEN
        if not token:
            raise ValueError("GITHUB_TOKEN not set")

        url = f"https://api.github.com/repos/{self.config.GITHUB_REPO}/releases"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }
        data = {
            "tag_name": tag,
            "name": name,
            "body": f"Release {name}",
            "prerelease": prerelease,
        }
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code >= 300:
            btul.logging.error("GitHub release failed:", resp.text)
        else:
            btul.logging.success("✅ GitHub release created.")

    def _resolve_components(self, targets):
        all_components = {
            "miner": [
                os.path.join("miner", d)
                for d in os.listdir("miner")
                if os.path.isdir(os.path.join("miner", d))
            ],
            "validator": [
                os.path.join("validator", d)
                for d in os.listdir("validator")
                if os.path.isdir(os.path.join("validator", d))
            ],
        }
        result = set()
        for target in targets:
            if target == ".":
                result.update(all_components["miner"])
                result.update(all_components["validator"])
            elif target in all_components:
                result.update(all_components[target])
            else:
                # component path like miner/component1
                if os.path.isdir(target):
                    result.add(target)
                else:
                    btul.logging.warning(f"⚠️ Skipping unknown target: {target}")
        return sorted(result)

    def _get_existing_tags(self):
        """Return a list of all Git tags in the current repository."""
        try:
            result = subprocess.run(
                ["git", "tag"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            tags = result.stdout.strip().split("\n")
            return [tag for tag in tags if tag]
        except subprocess.CalledProcessError as e:
            btul.logging.error("❌ Failed to get git tags:", e.stderr)
            return []


async def main():
    worker = None
    try:
        parser = argparse.ArgumentParser()
        btul.logging.add_args(parser)

        parser.add_argument(
            "--bump",
            type=str,
            choices=["patch", "minor", "major"],
            default=None,
            help="Type of version bump",
        )
        parser.add_argument(
            "--prerelease",
            type=str,
            choices=["alpha", "rc"],
            default=None,
            help="Optional pre-release tag",
        )
        parser.add_argument(
            "--targets",
            type=str,
            nargs="+",
            default=["."],
            help="Provide one or more targets you want to deploy (e.g., miner, validator, miner/neuron, etc)",
        )

        config = btcc.Config(parser)
        btul.logging(config=config, debug=True)
        btul.logging.set_trace(False)
        btul.logging._stream_formatter.set_trace(False)

        worker = Worker(config)
        worker.run()

    except ValueError as e:
        btul.logging.error(f"ValueError: {e}")
        btul.logging.debug(traceback.format_exc())

    finally:
        if worker:
            worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
