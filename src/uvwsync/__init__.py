# MIT License
#
# Copyright (c) 2025 Tom Rothamel <tom@rothamel.us>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import os
import pathlib
import tomllib
import sys
import subprocess

global path

def find_workspace() -> pathlib.Path:
    """
    Find the root directory of the UV workspace that contains the current directory.
    """

    current_dir = pathlib.Path.cwd()
    while current_dir != current_dir.parent:
        pyproject_path = current_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with pyproject_path.open("rb") as file:
                    config = tomllib.load(file)

                    try:
                        if config["tool"]["uv"]["workspace"]["members"]:
                            return current_dir
                    except KeyError:
                        pass

            except Exception as e:
                print(f"Error reading {pyproject_path}: {e}", file=sys.stderr)
                sys.exit(1)
        current_dir = current_dir.parent

    raise SystemExit("The current directory is not a UV workspace.")


def find_packages(package: str):
    """
    Finds all packages that the named package depends on by running the `uv export` command.
    """
    rv = []

    result = subprocess.run(
        ["uv", "export", "--package", package, "--all-groups"],
        text=True,
        capture_output=True,
        check=True
    )

    for line in result.stdout.splitlines():
        if line.startswith("-e ./"):
            packagename = line[5:].strip()
            rv.append(packagename)

    return rv


def get_extra_files(workspace: pathlib.Path) -> list[pathlib.Path]:
    """
    Returns a list of Path objects for files listed in tool.uvwsync.extra-files
    in the pyproject.toml file in the given workspace directory.
    If the key does not exist, returns an empty list.
    """
    pyproject_path = workspace / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    with pyproject_path.open("rb") as f:
        config = tomllib.load(f)

    try:
        files = config["tool"]["uvwsync"]["extra-files"]
    except KeyError:
        return []

    if not isinstance(files, list):
        raise SystemExit(f"Expected a list for 'tool.uvwsync.extra-files' in {pyproject_path}, got {type(files).__name__}.")

    return [workspace / pathlib.Path(f) for f in files]


def main():

    # unset VIRTUAL_ENV.
    os.environ.pop("VIRTUAL_ENV", None)

    ap = argparse.ArgumentParser()
    ap.add_argument("package", help="The name of the package to upload and sync.")
    ap.add_argument("destination", help="The destination to upload and sync the package to.")

    args = ap.parse_args()

    workspace = find_workspace()
    package: str = args.package
    destination: str = args.destination

    destination_host, _, destination_path = destination.rpartition(":")

    if not destination.endswith("/"):
        destination += "/"

    packages = set(find_packages(package))
    workset = set(packages)

    # Transitive closue of package dependencies, including build dependencies.
    while workset:
        p = workset.pop()
        new_packages = find_packages(p)
        for np in new_packages:
            if np not in packages:
                packages.add(np)
                workset.add(np)

    extra_files = get_extra_files(workspace)

    rsync_command = [
        "rsync",
        "-FF",
        "--delete",
        "-a",
        "--exclude",  ".*",
        "--include", ".python-version",
        workspace / "pyproject.toml",
        workspace / "uv.lock",
        workspace / ".python-version"
    ] + [workspace / pkg for pkg in sorted(packages)] + extra_files + [
        destination,
    ]

    rsync_command = [ str(arg) for arg in rsync_command ]

    try:
        subprocess.run(rsync_command, check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Error running 'rsync': {e}")

    if destination_host:
        ssh = [ "ssh", destination_host ]
        uv = ".local/bin/uv"
    else:
        ssh = [ ]
        uv = "uv"

    subprocess.run(ssh + [
        uv, "sync", "--package", package, "--directory", destination_path
    ], check=True)

    if (workspace / package / "after_deploy.sh").exists():
        subprocess.run(ssh + [ f"{destination_path}/{package}/after_deploy.sh"
        ], check=True)

print("UV")
