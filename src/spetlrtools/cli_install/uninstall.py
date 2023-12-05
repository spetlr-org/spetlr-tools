"""
- find the test job (by ID or discover by tag)
- get job status:
- tasks: pending: 0 running: 0 success: 0 failed: 0
- any time a task finishes, print the log
- add a fail_fast so that any time a task fails, job is cancelled
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
