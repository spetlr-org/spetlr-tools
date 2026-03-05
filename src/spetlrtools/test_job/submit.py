"""
usage: spetlr-test-job submit [-h] [--dry-run] [--wheels WHEELS] [--extras-require EXTRAS_REQUIRE] --tests TESTS [--task TASK] [--tasks-from TASKS_FROM]
                              [--serverless-task SERVERLESS_TASK] [--serverless-tasks-from SERVERLESS_TASKS_FROM] [--cluster CLUSTER | --cluster-file CLUSTER_FILE]
                              [--environment ENVIRONMENT | --environment-file ENVIRONMENT_FILE] [--sparklibs SPARKLIBS | --sparklibs-file SPARKLIBS_FILE]
                              [--requirement REQUIREMENT | --requirements-file REQUIREMENTS_FILE] [--main-script MAIN_SCRIPT] [--pytest-args PYTEST_ARGS] [--out-json OUT_JSON]
                              [--upload-to {workspace,dbfs}] [--wait-for-job]

Run Test Cases on databricks cluster.

options:
  -h, --help            show this help message and exit
  --dry-run             Don't do anything, only report
  --wheels WHEELS       The glob paths of all wheels under test.
  --extras-require EXTRAS_REQUIRE
                        The if given, the wheel will be installed with this like wheel[extras_require]. Used for test dependencies in *serverless only*.
  --tests TESTS         Location of the tests folder. Will be sent to databricks as a whole.
  --task TASK, --cluster-task TASK
                        Single Test file or folder to execute on a job cluster.
  --tasks-from TASKS_FROM, --cluster-tasks-from TASKS_FROM
                        path in test archive where each subfolder becomes a task to execute on a job cluster.
  --serverless-task SERVERLESS_TASK
                        Single Test file or folder to execute serverless.
  --serverless-tasks-from SERVERLESS_TASKS_FROM
                        path in test archive where each subfolder becomes a serverless task.
  --cluster CLUSTER     JSON document describing the cluster setup.
  --cluster-file CLUSTER_FILE
                        File with JSON document describing the cluster setup.
  --environment ENVIRONMENT
                        JSON document describing the serverless environment setup.
  --environment-file ENVIRONMENT_FILE
                        File with JSON document describing the serverless environment setup.
  --sparklibs SPARKLIBS
                        JSON document describing the spark dependencies.
  --sparklibs-file SPARKLIBS_FILE
                        File with JSON document describing the spark dependencies.
  --requirement REQUIREMENT
                        a python dependency, specified like for pip
  --requirements-file REQUIREMENTS_FILE
                        File with python dependencies, specified like for pip
  --main-script MAIN_SCRIPT
                        Your own test_main.py script file, to add custom functionality.
  --pytest-args PYTEST_ARGS
                        Additional arguments to pass to pytest in each test job.
  --out-json OUT_JSON   File to store the RunID for future queries.
  --upload-to {workspace,dbfs}
                        Where to upload test job files.
  --wait-for-job        After submission, wait for result using cli v2.

If cluster tasks are specified, the cluster description is mandatory. If serverless tasks are specified, the environment description is mandatory. At least one cluster task or
serverless task must be specified.
"""

import argparse
import inspect
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PosixPath
from textwrap import dedent
from typing import Dict, List, Union
from typing.io import IO

from spetlrtools.test_job import test_main
from spetlrtools.test_job.dbcli import DbCli
from spetlrtools.test_job.RemoteLocation import (
    DbfsLocation,
    RemoteLocation,
    StageArea,
    WorkspaceLocation,
)


# Custom action to handle the deprecation warning
class DeprecatedAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(
            f"WARNING: {option_string} is deprecated and will be removed in future versions."
        )


def setup_submit_parser(subparsers):
    """
    Adds a subparser for the command 'submit'.
    :param subparsers: must be the object returned by ArgumentParser().add_subparsers()
    :return:
    """

    parser: argparse.ArgumentParser = subparsers.add_parser(
        "submit",
        description="Run Test Cases on databricks cluster.",
        epilog=dedent("""\
        If cluster tasks are specified, the cluster description is mandatory.
        If serverless tasks are specified, the environment description is mandatory.
        At least one cluster task or serverless task must be specified.
        """),
    )
    parser.set_defaults(func=submit_main)

    parser.add_argument(
        "--dry-run", help="Don't do anything, only report", action="store_true"
    )

    parser.add_argument(
        "--wheels",
        type=str,
        required=False,
        help="The glob paths of all wheels under test.",
        default="dist/*.whl",
    )
    parser.add_argument(
        "--extras-require",
        type=str,
        required=False,
        help="The if given, the wheel will be installed with this like wheel[extras_require]."
        " Used for test dependencies in *serverless only*.",
    )

    parser.add_argument(
        "--tests",
        type=str,
        required=True,
        help="Location of the tests folder. Will be sent to databricks as a whole.",
    )

    parser.add_argument(
        "--task",
        "--cluster-task",
        help="Single Test file or folder to execute on a job cluster.",
        action="append",
    )
    parser.add_argument(
        "--tasks-from",
        "--cluster-tasks-from",
        help="path in test archive where each subfolder becomes a task to execute on a job cluster.",
        action="append",
    )

    parser.add_argument(
        "--serverless-task",
        help="Single Test file or folder to execute serverless.",
        action="append",
    )
    parser.add_argument(
        "--serverless-tasks-from",
        help="path in test archive where each subfolder becomes a serverless task.",
        action="append",
    )

    # cluster argument pair
    cluster = parser.add_mutually_exclusive_group(required=False)
    cluster.add_argument(
        "--cluster",
        type=str,
        help="JSON document describing the cluster setup.",
        default=None,
    )
    cluster.add_argument(
        "--cluster-file",
        type=argparse.FileType("r"),
        help="File with JSON document describing the cluster setup.",
    )

    # environment argument pair
    environment = parser.add_mutually_exclusive_group(required=False)
    environment.add_argument(
        "--environment",
        type=str,
        help="JSON document describing the serverless environment setup.",
        default=None,
    )
    environment.add_argument(
        "--environment-file",
        type=argparse.FileType("r"),
        help="File with JSON document describing the serverless environment setup.",
    )

    # spark libraries argument pair
    sparklibs = parser.add_mutually_exclusive_group(required=False)
    sparklibs.add_argument(
        "--sparklibs",
        help="JSON document describing the spark dependencies.",
    )
    sparklibs.add_argument(
        "--sparklibs-file",
        type=argparse.FileType("r"),
        help="File with JSON document describing the spark dependencies.",
    )

    # python dependencies file
    pydep = parser.add_mutually_exclusive_group(required=False)
    pydep.add_argument(
        "--requirement",
        action="append",
        help="a python dependency, specified like for pip",
        default=[],
    )
    pydep.add_argument(
        "--requirements-file",
        type=argparse.FileType("r"),
        help="File with python dependencies, specified like for pip",
    )

    parser.add_argument(
        "--main-script",
        type=argparse.FileType("r"),
        help="Your own test_main.py script file, to add custom functionality.",
    )

    parser.add_argument(
        "--pytest-args", help="Additional arguments to pass to pytest in each test job."
    )

    parser.add_argument(
        "--out-json",
        type=argparse.FileType("w"),
        help="File to store the RunID for future queries.",
    )

    parser.add_argument(
        "--upload-to",
        choices=["workspace", "dbfs"],
        help="Where to upload test job files.",
        default="dbfs",
    )

    parser.add_argument(
        "--wait-for-job",
        action="store_true",
        help="After submission, wait for result using cli v2.",
    )
    parser.add_argument("--wait", action=DeprecatedAction, help=argparse.SUPPRESS)

    return


def collect_arguments(args):
    """
    Post process the parsed arguments of the 'submit' command argument parser.
    :param args: parsed arguments of the 'submit' command argument parser
    :return:
    """

    # pre-process 'cluster'
    if args.cluster_file:
        args.cluster = args.cluster_file.read()
    if args.cluster:
        args.cluster = json.loads(args.cluster)

    # pre-process 'environment'
    if args.environment_file:
        args.environment = args.environment_file.read()
    if args.environment:
        args.environment = json.loads(args.environment)

    # pre-process 'sparklibs'
    if args.sparklibs_file:
        args.sparklibs = args.sparklibs_file.read()
    if args.sparklibs:
        args.sparklibs = json.loads(args.sparklibs)

    # pre-process 'requirement'
    if args.requirements_file:
        args.requirement = [
            line.strip()
            for line in args.requirements_file.read().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    args.pytest_args = (args.pytest_args or "").split()

    return args


def submit_main(args):
    """the main function of the cli command 'submit'. Not to be used directly."""

    args = collect_arguments(args)

    submit(
        test_path=args.tests,
        cluster=args.cluster,
        environment=args.environment,
        wheels=args.wheels,
        extras_require=args.extras_require,
        cluster_tasks=args.task,  # note argument has no 's'
        cluster_tasks_from=args.tasks_from,
        serverless_tasks=args.serverless_task,  # note argument has no 's'
        serverless_tasks_from=args.serverless_tasks_from,
        requirement=args.requirement,
        sparklibs=args.sparklibs,
        out_json=args.out_json,
        main_script=args.main_script,
        pytest_args=args.pytest_args,
        dry_run=args.dry_run,
        upload_to=args.upload_to,
        wait_for_job=args.wait_for_job,
    )


def verify_and_resolve_task(test_path: str, task: Union[str, PosixPath]):
    test_archive = PosixPath(test_path).resolve().absolute()

    task_path = PosixPath(task)
    if not task_path.is_absolute():
        task_path = (test_archive.parent / task_path).resolve().absolute()

    task_path = task_path.resolve().absolute()

    if not (test_archive == task_path or test_archive in task_path.parents):
        raise AssertionError(f"task {task} is not contained in {test_path}")

    if not task_path.exists():
        raise AssertionError(f"task {task_path} does not exist")

    if not (test_archive.parent / task).exists():
        raise AssertionError(f"The task {task} was not found in the test location.")

    return task_path.relative_to(test_archive.parent).as_posix()


def discover_job_tasks(test_path: str, folder: str):
    """If folder is given, create parallel tasks from this level.
    Otherwise, simply return the top folder as the single task.
    Returns a list of strings with the subfolders to process.
    """

    test_archive_parent = PosixPath(test_path).resolve().absolute().parent

    subfolders = [
        verify_and_resolve_task(test_path, x)
        for x in (test_archive_parent / folder).iterdir()
        if (x.is_dir() and not x.stem.startswith("_"))
    ]
    return subfolders


class PoolBoy:
    """Hold a list of available instance pools and replace the by-name reference with an id if possible."""

    MARKER = "instance-pool://"

    def __init__(self):
        self._lookup = self.get_instance_pools()

    def lookup(self, pool_id: str) -> str:
        if pool_id.startswith(self.MARKER):
            pool_name = pool_id[len(self.MARKER) :]
            return self._lookup[pool_name]
            # if this throws a KeyError, we are right to abort execution since the input is invalid.
        else:
            # No Marker = no lookup
            return pool_id

    def get_instance_pools(self) -> Dict[str, str]:
        pool_lookup = {
            pool.instance_pool_name: pool.instance_pool_id
            for pool in DbCli().list_instance_pools()
        }
        return pool_lookup


def submit(
    test_path: str,
    wheels: str,
    extras_require: str = None,
    cluster: dict = None,
    environment: dict = None,
    cluster_tasks: List[str] = None,
    cluster_tasks_from: List[str] = None,
    serverless_tasks: List[str] = None,
    serverless_tasks_from: List[str] = None,
    requirement: List[str] = None,
    sparklibs: List[dict] = None,
    out_json: IO[str] = None,
    main_script: IO[str] = None,
    pytest_args: List[str] = None,
    dry_run=False,
    upload_to="dbfs",
    wait_for_job=False,
):
    """
    --wheels WHEELS       The glob paths of all wheels under test.
    --extras-require EXTRAS_REQUIRE
                          The if given, the wheel will be installed with this like wheel[extras_require]. Used for test dependencies in *serverless only*.
    --tests TESTS         Location of the tests folder. Will be sent to databricks as a whole.
    --task TASK, --cluster-task TASK
                          Single Test file or folder to execute on a job cluster.
    --tasks-from TASKS_FROM, --cluster-tasks-from TASKS_FROM
                          path in test archive where each subfolder becomes a task to execute on a job cluster.
    --serverless-task SERVERLESS_TASK
                          Single Test file or folder to execute serverless.
    --serverless-tasks-from SERVERLESS_TASKS_FROM
                          path in test archive where each subfolder becomes a serverless task.
    --cluster CLUSTER     JSON document describing the cluster setup.
    --cluster-file CLUSTER_FILE
                          File with JSON document describing the cluster setup.
    --environment ENVIRONMENT
                          JSON document describing the serverless environment setup.
    --environment-file ENVIRONMENT_FILE
                          File with JSON document describing the serverless environment setup.
    --sparklibs SPARKLIBS
                          JSON document describing the spark dependencies.
    --sparklibs-file SPARKLIBS_FILE
                          File with JSON document describing the spark dependencies.
    --requirement REQUIREMENT
                          a python dependency, specified like for pip
    --requirements-file REQUIREMENTS_FILE
                          File with python dependencies, specified like for pip
    --main-script MAIN_SCRIPT
                          Your own test_main.py script file, to add custom functionality.
    --pytest-args PYTEST_ARGS
                          Additional arguments to pass to pytest in each test job.
    --out-json OUT_JSON   File to store the RunID for future queries.
    --upload-to {workspace,dbfs}
                          Where to upload test job files.
    --wait-for-job        After submission, wait for result using cli v2.
    """
    if requirement is None:
        requirement = []
    if sparklibs is None:
        sparklibs = []
    if pytest_args is None:
        pytest_args = []
    if cluster_tasks is None:
        cluster_tasks = []
    if cluster_tasks_from is None:
        cluster_tasks_from = []
    if serverless_tasks is None:
        serverless_tasks = []
    if serverless_tasks_from is None:
        serverless_tasks_from = []
    if not (
        cluster_tasks or cluster_tasks_from or serverless_tasks or serverless_tasks_from
    ):
        raise ValueError("No tasks given")
    if cluster_tasks or cluster_tasks_from:
        # check the structure of the cluster object
        if not isinstance(cluster, dict):
            raise AssertionError("invalid cluster specification")
    if serverless_tasks or serverless_tasks_from:
        # check the structure of the cluster object
        if not isinstance(environment, dict):
            raise AssertionError("invalid environment specification")

    upload_to = upload_to.lower()

    # check the structure of the sparklibs object
    if not isinstance(sparklibs, list):
        raise AssertionError("invalid sparklibs specification")

    if environment is not None:
        # serverless is being used
        try:
            if "dependencies" not in environment["spec"]:
                environment["spec"]["dependencies"] = []
        except KeyError:
            print("ERROR: The specified environment is not of the expected structure")
            print(dedent("""Expectation was something like:
                {
                  "environment_key": "myname",
                  "spec": {
                    "dependencies": [
                      "spetlr>=16.4.9"
                    ],
                    "environment_version": "3"
                  }
                }"""))
            raise

    for py_requirement in requirement:
        sparklibs.append({"pypi": {"package": py_requirement}})
        if environment:
            environment["spec"]["dependencies"].append(py_requirement)

    dbcli = DbCli()

    # create everything in a temporary directory.
    # for dry-runs, keep make it a local directory and keep it
    with StageArea(dry_run) as stage:
        if upload_to == "workspace":
            remote: RemoteLocation = WorkspaceLocation(stage)
        elif upload_to == "dbfs":
            remote: RemoteLocation = DbfsLocation(stage)
        else:
            raise ValueError("unsupported upload")

        wheels = discover_wheels(wheels, remote)

        extras_require_appendix = f"[{extras_require}]" if extras_require else ""
        for wheel in wheels:
            sparklibs.append({"whl": wheel})
            if environment:
                environment["spec"]["dependencies"].append(
                    wheel + extras_require_appendix
                )

        prepare_archive(test_path, remote)
        main_file = prepare_main_file(remote, main_script)

        resolved_tasks = [
            verify_and_resolve_task(test_path, task) for task in cluster_tasks
        ]
        for task in cluster_tasks_from:
            # subtasks will be ['tests/cluster/job1', 'tests/cluster/job2'] or similar
            resolved_tasks += discover_job_tasks(test_path, task)

        resolved_serverless_tasks = [
            verify_and_resolve_task(test_path, task) for task in serverless_tasks
        ]
        for task in serverless_tasks_from:
            # subtasks will be ['tests/cluster/job1', 'tests/cluster/job2'] or similar
            resolved_serverless_tasks += discover_job_tasks(test_path, task)

        if dry_run:
            print("resolved_tasks =", resolved_tasks)
            print("resolved_serverless_tasks =", resolved_serverless_tasks)

        if resolved_tasks and "instance_pool_id" in cluster:
            cluster["instance_pool_id"] = PoolBoy().lookup(cluster["instance_pool_id"])

        # construct the workflow object
        workflow = dict(run_name="Testing Run", format="MULTI_TASK", tasks=[])

        for task in resolved_tasks:
            # construct a task name from the test task file path
            task_sub = re.sub(r"[^a-zA-Z0-9_-]", "_", task)

            workflow["tasks"].append(
                dict(
                    task_key=task_sub,
                    libraries=sparklibs,
                    max_retries=0,
                    spark_python_task=dict(
                        python_file=main_file,
                        parameters=[
                            # running in the spark python interpreter, the python __file__ variable does not
                            # work. Hence, we need to tell the script where the test area is.
                            f"--basedir={remote.remote_base()}",
                            # we can actually run any part of our test suite, but some files need the full repo.
                            # Only run tests from this folder.
                            f"--folder={task}",
                            # additional arguments to pass to pytest
                            f"--pytestargs={json.dumps(pytest_args)}",
                        ],
                    ),
                    new_cluster=cluster,
                )
            )

        if resolved_serverless_tasks:
            workflow["environments"] = []

        for task in resolved_serverless_tasks:
            # construct a task name from the test task file path
            task_sub = re.sub(r"[^a-zA-Z0-9_-]", "_", task)

            task_environment = environment.copy()
            task_environment["environment_key"] = task_sub
            workflow["environments"].append(task_environment)

            workflow["tasks"].append(
                dict(
                    task_key=task_sub,
                    spark_python_task=dict(
                        python_file=main_file,
                        parameters=[
                            # running in the spark python interpreter, the python __file__ variable does not
                            # work. Hence, we need to tell the script where the test area is.
                            f"--basedir={remote.remote_base()}",
                            # we can actually run any part of our test suite, but some files need the full repo.
                            # Only run tests from this folder.
                            f"--folder={task}",
                            # additional arguments to pass to pytest
                            f"--pytestargs={json.dumps(pytest_args)}",
                        ],
                    ),
                    max_retries=0,
                    environment_key=task_sub,
                )
            )

        jobfile = remote.new_local_file("job.json").local

        with open(jobfile, "w") as f:
            json.dump(workflow, f, indent=2)

        remote.upload(dry_run)

        if wait_for_job:
            print("handing control to databricks jobs submit ...")
            dbcli.execv_run_file(jobfile, dry_run=dry_run)
            # the above function ends python and does not return
            return

        try:
            print("Submitting job...")
            run_id = dbcli.submit(workflow, dry_run=dry_run)
        except subprocess.CalledProcessError:
            print("Json contents:")
            print(json.dumps(workflow, indent=4))
            raise

    # now we have the run_id
    print(f"Started run with ID {run_id}")
    print(f"Follow job details at {dbcli.get_run(run_id).run_page_url}")

    if out_json:
        json.dump({"run_id": run_id}, out_json)


def discover_wheels(globpath: str, remote: RemoteLocation) -> List[str]:
    """Find all wheel files in the globpath and add them to the remote location."""
    result = []
    for item in Path().glob(globpath):
        result.append(remote.add_local_path(str(item), "libs"))

    return result


def prepare_archive(test_path: str, remote: RemoteLocation):
    """Zip the test archive and add it to the staging area"""
    print(f"now archiving {test_path}")

    with tempfile.TemporaryDirectory() as tempdir:
        real_archive_path = shutil.make_archive(
            str(Path(tempdir) / "tests"),
            "zip",
            Path(test_path) / "..",
            base_dir=Path(test_path).parts[-1],
        )

        # it seems the doing a workspace import-dir on a zip archive will unpack it locally to upload.
        # so we need to trick it by renaming the file
        renamed_archive_path = Path(real_archive_path).with_suffix(".archive")
        shutil.move(real_archive_path, renamed_archive_path)

        return remote.add_local_path(str(renamed_archive_path))


def prepare_main_file(remote: RemoteLocation, main_script: IO[str] = None) -> str:
    print("now preparing test main file")

    main_ref = remote.new_local_file("main.py")

    with open(main_ref.local, "w") as f:
        if main_script:
            f.write(main_script.read())
        else:
            print("Using default main script test_main.py")
            f.write(inspect.getsource(test_main))

    return main_ref.remote
