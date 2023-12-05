"""
- find the test job (by ID or discover by tag)
- get job status:
- tasks: pending: 0 running: 0 success: 0 failed: 0
- any time a task finishes, print the log
- add a fail_fast so that any time a task fails, job is cancelled
"""
import argparse
import io
import os
import platform
import re
import subprocess
import sys
import zipfile

import requests

from spetlrtools.cli_install.defaults import (
    _DATABRICKS_CLI_REPO,
    _DEFAULT_TARGET,
    isWin,
)
from spetlrtools.cli_install.latest import get_latest_version
from spetlrtools.cli_install.uninstall import uninstall


def setup_install_parser(subparsers):
    """
    Adds a subparser for the command 'install'.
    :param subparsers: must be the object returned by ArgumentParser().add_subparsers()
    :return:
    """
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "install", description="Install the datbricks cli v2 to your python area."
    )
    parser.set_defaults(func=install_main)

    parser.add_argument(
        "--version",
        type=str,
        help="Version of CLI to install (accepts @file), defaults to latest.",
        default=None,
    )

    parser.add_argument(
        "--target",
        type=str,
        help="path of the installed cli",
        default=_DEFAULT_TARGET,
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove other versions present.",
        default=False,
    )


def install_main(args):
    """
    Main function of the 'install' command. Only to be used via the cli.
    :param args: the parsed arguments from the install subparser
    :return:
    """

    # Post process the arguments
    if args.force:
        # uninstall silently
        uninstall(args.target)

    if install(version=args.version, target=args.target):
        print("Installation failed")
        sys.exit(-1)


def determine_platform():
    details = platform.uname()
    if re.match(".*windows.*", details.system, flags=re.IGNORECASE):
        system = "_windows"
    elif re.match(".*darwin.*", details.system, flags=re.IGNORECASE):
        system = "_darwin"
    elif re.match(".*linux.*", details.system, flags=re.IGNORECASE):
        system = "_linux"
    else:
        raise Exception("Unknown system platform")

    if re.match(".*64.*", details.machine):
        arch = "_amd64"
    else:
        arch = "_386"

    return system + arch


def install(version: str = None, target=None):
    """Install main function."""
    version = version or get_latest_version()
    if version.startswith("@"):
        print(f"Version information taken from {version[1:]}")
        version = open(version[1:]).read().strip()

    system = determine_platform()
    file_name = f"databricks_cli_{version}{system}"

    target = target or _DEFAULT_TARGET

    if target.exists():
        raise Exception(f"Target {str(target)} exists. Please uninstall first.")

    if not target.parent.exists():
        raise Exception(
            f"Installation target directory does not exits {str(target.parent)}"
        )

    with open(target, "wb") as t:
        r = requests.get(
            f"{_DATABRICKS_CLI_REPO}/releases/download/v{version}/{file_name}.zip"
        )
        z = zipfile.ZipFile(io.BytesIO(r.content))

        (db_exe_file,) = [n for n in z.namelist() if n.startswith("databricks")]
        t.write(z.read(db_exe_file))

    if not isWin():
        os.chmod(target, 0o755)

    subprocess.run([target, "--version"])
