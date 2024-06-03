import os
import unittest
from pathlib import Path
from unittest.mock import create_autospec

import git
from databricks.sdk import WorkspaceClient

from spetlrtools.test_job.dbcli import DbCli
from spetlrtools.test_job.RemoteLocation import (
    RemoteLocation,
    StageArea,
    WorkspaceLocation,
)
from spetlrtools.test_job.submit import (
    discover_wheels,
    prepare_archive,
    prepare_main_file,
)

repoRoot = git.Repo(search_parent_directories=True).working_dir


class JobSumitToolTest(unittest.TestCase):
    def assert_file_under_parent(self, filename: str, parent: str):
        found = False
        for root, dirs, files in os.walk(parent):
            if any(file == filename for file in files):
                found = True
                break
        self.assertTrue(found, f"File '{filename}' does not exist within staging area.")

    @classmethod
    def setUpClass(cls) -> None:
        DbCli.w = create_autospec(WorkspaceClient)
        DbCli.w.current_user.me.return_value.user_name = "hello@world.com"

        os.chdir(repoRoot)

        # prepare a wheel file that will go into the test job
        dist = Path(repoRoot) / "dist"
        dist.mkdir(exist_ok=True)
        with open(dist / "dummy.whl", "w") as f:
            f.write("Some data")

    def test_01_prepare_archive(self):
        with StageArea() as stage:
            remote: RemoteLocation = WorkspaceLocation(stage)
            prepare_archive("tests", remote)
            self.assert_file_under_parent("tests.archive", stage)

    def test_prepare_main_file(self):
        with StageArea() as stage:
            remote: RemoteLocation = WorkspaceLocation(stage)
            prepare_main_file(remote)
            self.assert_file_under_parent("main.py", stage)

    def test_discover_wheels(self):
        with StageArea() as stage:
            remote: RemoteLocation = WorkspaceLocation(stage)
            discover_wheels("dist/*.whl", remote)
            self.assert_file_under_parent("dummy.whl", stage)
