"""
- find the test job (by ID or discover by tag)
- get job status:
- tasks: pending: 0 running: 0 success: 0 failed: 0
- any time a task finishes, print the log
- add a fail_fast so that any time a task fails, job is cancelled
"""

import argparse
import json
import sys
from typing import IO


def setup_fetch_parser(subparsers):
    """
    Adds a subparser for the command 'fetch'.
    :param subparsers: must be the object returned by ArgumentParser().add_subparsers()
    :return:
    """
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "fetch", description="Return test run result."
    )
    parser.set_defaults(func=fetch_main)

    # cluster argument pair
    runid_config = parser.add_mutually_exclusive_group(required=True)
    runid_config.add_argument(
        "--runid",
        type=int,
        help="Run ID of the test job",
        default=None,
    )
    runid_config.add_argument(
        "--runid-json",
        type=argparse.FileType("r"),
        help="File with JSON document describing the Run ID of the test job.",
        default=None,
    )

    parser.add_argument(
        "--stdout",
        type=argparse.FileType("w"),
        required=False,
        help="Output test stdout to this file.",
        default=None,
    )

    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Stop and cancel job on first failed task.",
    )


def collect_args(args):
    """Post process the arguments of the ."""
    if args.runid is None:
        args.runid = json.load(args.runid_json)["run_id"]

    return args


def fetch_main(args):
    """
    Main function of the 'fetch' command. Only to be used via the cli.
    :param args: the parsed arguments from the fetch subparser
    :return:
    """

    # Post process the arguments
    if args.runid is None:
        args.runid = json.load(args.runid_json)["run_id"]

    if fetch(args.runid, args.stdout, args.failfast):
        print("Run failed")
        sys.exit(-1)


def fetch(run_id: int, stdout_file: IO[str] = None, failfast=False):
    """Fetch main function.
    See the cli help for parameter descriptions and functionality.
    Can be used programmatically."""
    raise NotImplementedError()
