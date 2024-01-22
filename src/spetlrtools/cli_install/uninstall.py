"""
This script is dedicated to the uninstallation of the Databricks CLI tool. Its main features include:
- Setting up a subparser for the 'uninstall' command, allowing the user to specify the target path for uninstallation.
- The main function for the 'uninstall' command, which executes the uninstallation process.
- The core uninstall function, which attempts to remove the Databricks CLI using system commands and
    handles the deletion of the target executable file.

This script is particularly useful for cleanly removing the Databricks CLI from a system, ensuring that
    no residual files are left behind. It utilizes the 'subprocess' module to execute system-level commands
    and 'argparse' for command-line argument parsing.

Note: This script should be run through the command line interface and assumes proper permissions for
    uninstallation tasks.
"""

import argparse
import os
import subprocess
import sys

from spetlrtools.cli_install.defaults import _DEFAULT_TARGET


def setup_uninstall_parser(subparsers):
    """
    Adds a subparser for the command 'install'.
    :param subparsers: must be the object returned by ArgumentParser().add_subparsers()
    :return:
    """
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "uninstall", description="remove the databricks cli."
    )
    parser.set_defaults(func=uninstall_main)

    parser.add_argument(
        "--target",
        type=str,
        help="path of the installed cli",
        default=_DEFAULT_TARGET,
    )


def uninstall_main(args):
    """
    Main function of the 'uninstall' command. Only to be used via the cli.
    :param args: the parsed arguments from the install subparser
    :return:
    """

    if uninstall(target=args.target):
        print("Uninstallation failed")
        sys.exit(-1)


def uninstall(target=None):
    """Uninstall main function."""

    try:
        subprocess.run(
            ["pip", "uninstall", "databricks-cli", "-y"],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        "it seems cli v1 was not installed."

    target = target or _DEFAULT_TARGET
    if target.exists():
        os.unlink(target)
