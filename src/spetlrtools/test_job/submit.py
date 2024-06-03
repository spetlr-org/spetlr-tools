"""
usage: spetlr-test-job submit [-h] [--dry-run] [--wheels WHEELS] --tests TESTS [--task TASK] [--tasks-from TASKS_FROM] (--cluster CLUSTER | --cluster-file CLUSTER_FILE)
                              [--sparklibs SPARKLIBS | --sparklibs-file SPARKLIBS_FILE] [--requirement REQUIREMENT | --requirements-file REQUIREMENTS_FILE] [--main-script MAIN_SCRIPT] [--pytest-args PYTEST_ARGS]
                              [--out-json OUT_JSON] [--wait-for-job]

Run Test Cases on databricks cluster.

optional arguments:
  -h, --help            show this help message and exit
  --dry-run             Don't do anything, only report
  --wheels WHEELS       The glob paths of all wheels under test.
  --tests TESTS         Location of the tests folder. Will be sent to databricks as a whole.
  --task TASK           Single Test file or folder to execute.
  --tasks-from TASKS_FROM
                        path in test archive where each subfolder becomes a task.
  --cluster CLUSTER     JSON document describing the cluster setup.
  --cluster-file CLUSTER_FILE
                        File with JSON document describing the cluster setup.
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

import argparse
import inspect
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PosixPath
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
        "submit", description="Run Test Cases on databricks cluster."
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
        "--tests",
        type=str,
        required=True,
        help="Location of the tests folder. Will be sent to databricks as a whole.",
    )

    parser.add_argument(
        "--task", help="Single Test file or folder to execute.", action="append"
    )
    parser.add_argument(
        "--tasks-from",
        help="path in test archive where each subfolder becomes a task.",
        action="append",
    )

    # cluster argument pair
    cluster = parser.add_mutually_exclusive_group(required=True)
    cluster.add_argument(
        "--cluster",
        type=str,
        help="JSON document describing the cluster setup.",
    )
    cluster.add_argument(
        "--cluster-file",
        type=argparse.FileType("r"),
        help="File with JSON document describing the cluster setup.",
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
    args.cluster = json.loads(args.cluster)

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
        wheels=args.wheels,
        tasks=args.task,
        tasks_from=args.tasks_from,
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
    cluster: dict,
    wheels: str,
    tasks: List[str] = None,
    tasks_from: List[str] = None,
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
    --dry-run             Don't do anything, only report
    --wheels WHEELS       The glob paths of all wheels under test.
    --tests TESTS         Location of the tests folder. Will be sent to databricks as a whole.
    --task TASK           Single Test file or folder to execute.
    --tasks-from TASKS_FROM
                          path in test archive where each subfolder becomes a task.
    --cluster CLUSTER     JSON document describing the cluster setup.
    --cluster-file CLUSTER_FILE
                          File with JSON document describing the cluster setup.
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
    if tasks is None:
        tasks = []
    if tasks_from is None:
        tasks_from = []
    if not (tasks or tasks_from):
        raise ValueError("No tasks given")
    upload_to = upload_to.lower()

    # check the structure of the cluster object
    if not isinstance(cluster, dict):
        raise AssertionError("invalid cluster specification")

    # check the structure of the sparklibs object
    if not isinstance(sparklibs, list):
        raise AssertionError("invalid sparklibs specification")

    for py_requirement in requirement:
        sparklibs.append({"pypi": {"package": py_requirement}})

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
        for wheel in wheels:
            sparklibs.append({"whl": wheel})

        prepare_archive(test_path, remote)
        main_file = prepare_main_file(remote, main_script)

        resolved_tasks = [verify_and_resolve_task(test_path, task) for task in tasks]
        for task in tasks_from:
            # subtasks will be ['tests/cluster/job1', 'tests/cluster/job2'] or similar
            resolved_tasks += discover_job_tasks(test_path, task)

        if dry_run:
            print(resolved_tasks)

        if "instance_pool_id" in cluster:
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
