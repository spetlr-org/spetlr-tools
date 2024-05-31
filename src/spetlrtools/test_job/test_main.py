"""
This is the default main file that is pushed to databricks to launch the test task.
Its tasks are
- to unpack the test archive,
- print a sequence of marker characters to identify the start
  of python executing in the output
- run the tests using pytest
This file is not intended to be used directly.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def test_main():
    """Main function to be called inside the test job task. Do not use directly."""
    parser = argparse.ArgumentParser(description="Run Test Cases.")

    # location to use for current run. Usually the cluster logs base folder
    parser.add_argument("--basedir")

    # relative path of test folder in test archive
    parser.add_argument("--folder")

    # archive of test files to use
    parser.add_argument("--pytestargs")

    args = parser.parse_args()

    extra_args = json.loads(args.pytestargs)

    # move to basedir so that simple imports from one test to another work
    basedir: str = args.basedir
    if basedir.startswith("dbfs:"):
        basedir = "/dbfs" + basedir[5:]
    # the basedir folder should exist because it is also the log destination
    # however we have seen cases where it does not exist yet at the start of the job,
    # so let's create it.

    with TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        sys.path = [tmpdir] + sys.path

        # unzip test archive to base folder
        shutil.copy(Path(basedir) / "tests.archive", "tests.zip")
        shutil.unpack_archive("tests.zip")
        os.unlink("tests.zip")

        # Ensure Spark is initialized before any tests are run
        # the import statement is inside the function so that the outer file
        # can be imported even where pyspark may not be available
        from spetlr.spark import Spark

        Spark.get()

        retcode = pytest.main(["-x", args.folder, *extra_args])
        if retcode.value:
            raise Exception("Pytest failed")


if __name__ == "__main__":
    test_main()
