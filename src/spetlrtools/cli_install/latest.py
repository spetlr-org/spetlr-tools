"""
- find the test job (by ID or discover by tag)
- get job status:
- tasks: pending: 0 running: 0 success: 0 failed: 0
- any time a task finishes, print the log
- add a fail_fast so that any time a task fails, job is cancelled
"""
import argparse
import sys

import requests


def setup_latest_parser(subparsers):
    """
    Adds a subparser for the command 'install'.
    :param subparsers: must be the object returned by ArgumentParser().add_subparsers()
    :return:
    """
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "latest", description="Get the latest cli version."
    )
    parser.set_defaults(func=latest_main)


def latest_main(args):
    """
    Main function of the 'uninstall' command. Only to be used via the cli.
    :param args: the parsed arguments from the install subparser
    :return:
    """

    latest_version = get_latest_version()
    if latest_version:
        print(latest_version)
    else:
        print("Fetching latest version failed")
        sys.exit(-1)


def get_latest_version():
    """Uninstall main function."""
    r = requests.get(
        "https://raw.githubusercontent.com/databricks/setup-cli/main/VERSION"
    )
    return r.content.decode("utf-8").strip()
