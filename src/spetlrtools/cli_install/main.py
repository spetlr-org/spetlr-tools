"""
This script acts as the primary entry point for a Databricks-related CLI tool. It orchestrates various commands
including:
- Setting up the CLI environment and parsing command-line arguments.
- Integrating subparsers for 'install', 'uninstall', and 'latest' commands, linking to their respective functionalities.
- Handling the execution flow based on the command chosen by the user.

The script leverages 'argparse' for command-line parsing, providing a user-friendly interface for interacting with the
 Databricks CLI tool. It is designed to be invoked from the command line and not intended for
 use as a module in other Python scripts.

Overall, this script simplifies the user interaction with the Databricks CLI tool,
offering a streamlined way to install, uninstall, and check for updates directly from the command line.
"""

import argparse

from spetlrtools.cli_install.install import setup_install_parser
from spetlrtools.cli_install.latest import setup_latest_parser
from spetlrtools.cli_install.uninstall import setup_uninstall_parser


def main():
    """Cli main function. Not for use from python."""
    parser = argparse.ArgumentParser(
        description="Run Test Cases on databricks cluster."
    )

    subparsers = parser.add_subparsers(required=True, dest="command")

    setup_install_parser(subparsers)
    setup_uninstall_parser(subparsers)
    setup_latest_parser(subparsers)

    args = parser.parse_args()
    args.func(args)
