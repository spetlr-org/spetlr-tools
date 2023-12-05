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
