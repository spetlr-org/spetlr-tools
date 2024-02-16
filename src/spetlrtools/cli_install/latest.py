"""
This script provides functionality for managing the installation process of a CLI tool.
It includes commands to fetch the latest version of the CLI. Key functionalities include:
- Adding a subparser for the 'latest' command to check for the latest version of the CLI.
- A main function for the 'latest' command, which fetches and prints the latest CLI version.
- A utility function to retrieve the latest version from a specified URL.

Note: This script is intended to be used as a part of a larger CLI tool and should
 be invoked through the command line interface.
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
