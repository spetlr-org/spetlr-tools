import io
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from textwrap import dedent
from unittest.mock import create_autospec

import git
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs

from spetlrtools.test_job.dbcli import DbCli
from spetlrtools.test_job.fetch import fetch
from spetlrtools.test_job.RemoteLocation import (
    RemoteLocation,
    StageArea,
    WorkspaceLocation,
)
from spetlrtools.test_job.submit import (
    discover_wheels,
    prepare_archive,
    prepare_main_file,
    submit,
)

repoRoot = git.Repo(search_parent_directories=True).working_dir


class JobSumitToolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        DbCli.w = create_autospec(WorkspaceClient)
        DbCli.w.current_user.me.return_value.user_name = "hello@world.com"

        RemoteLocation.date = "<<right about now>>"

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
            self.assertTrue(
                (
                    Path(stage)
                    / ".spetlr"
                    / "test"
                    / "<<right about now>>"
                    / "tests.archive"
                ).exists(),
                msg="Could not find staged tests.archive",
            )

    def test_prepare_main_file(self):
        with StageArea() as stage:
            remote: RemoteLocation = WorkspaceLocation(stage)
            prepare_main_file(remote)
            self.assertTrue(
                (
                    Path(stage) / ".spetlr" / "test" / "<<right about now>>" / "main.py"
                ).exists(),
                msg="Could not find staged main file",
            )

    def test_discover_wheels(self):
        with StageArea() as stage:
            remote: RemoteLocation = WorkspaceLocation(stage)
            discover_wheels("dist/*.whl", remote)
            self.assertTrue(
                (
                    Path(stage)
                    / ".spetlr"
                    / "test"
                    / "<<right about now>>"
                    / "libs"
                    / "dummy.whl"
                ).exists(),
                msg="Could not find staged library",
            )

    def test_submit(self):
        submit(
            test_path="tests/",
            tasks=["tests/unit/"],
            cluster={"dummy": "value"},
            wheels="dist/*.whl",
            upload_to="dbfs",
            no_wait=True,
        )
        args, kwargs = DbCli.w.jobs._api.do.call_args
        body_arg = kwargs["body"]
        self.assertEquals(
            body_arg,
            dict(
                run_name="Testing Run",
                format="MULTI_TASK",
                tasks=[
                    {
                        "task_key": "tests_unit",
                        "libraries": [
                            {
                                "whl": "dbfs:/spetlr/test/hello@world.com/<<right about now>>/libs/dummy.whl"
                            }
                        ],
                        "spark_python_task": {
                            "python_file": "dbfs:/spetlr/test/hello@world.com/<<right about now>>/main.py",
                            "parameters": [
                                "--basedir=dbfs:/spetlr/test/hello@world.com/<<right about now>>",
                                "--folder=tests/unit",
                                "--pytestargs=[]",
                            ],
                        },
                        "new_cluster": {"dummy": "value"},
                    }
                ],
            ),
        )

    def test_fetch(self):
        run_details = jobs.Run(
            run_id=123456,
            run_page_url="https://url.to.run",
            state=jobs.RunState(
                life_cycle_state=jobs.RunLifeCycleState.TERMINATED,
                result_state=jobs.RunResultState.SUCCESS,
            ),
            tasks=[
                jobs.RunTask(
                    task_key="yo_momma",
                    state=jobs.RunState(
                        life_cycle_state=jobs.RunLifeCycleState.TERMINATED,
                        result_state=jobs.RunResultState.SUCCESS,
                    ),
                )
            ],
        )
        DbCli.w.jobs.get_run.return_value = run_details
        out = jobs.RunOutput(logs="Here be Dragons!!")
        DbCli.w.jobs.get_run_output.return_value = out

        f = io.StringIO()
        with redirect_stdout(f):
            fetch(run_id=123456)

        out = f.getvalue()
        self.assertEquals(
            out,
            dedent(
                """\
            Job details: https://url.to.run
            Overall state: SUCCESS | Task states: SUCCESS: 1
            Getting stdout for yo_momma
            Here be Dragons!!
            Run result SUCCESS!
            """
            ),
        )
