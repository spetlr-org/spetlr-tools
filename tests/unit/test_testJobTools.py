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
            cluster_tasks=["tests/unit/"],
            cluster={"dummy": "value"},
            wheels="dist/*.whl",
            upload_to="dbfs",
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
                        "max_retries": 0,
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
                    attempt_number=1,
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
            dedent("""\
            Job details: https://url.to.run
            Overall state: SUCCESS | Task states: SUCCESS: 1
            Getting stdout for yo_momma
            Here be Dragons!!
            Run result SUCCESS!
            """),
        )


# TODO: Extend fetch so that it can accept this status result
# This is a job that faild due to external api status and was retried
# manually and is still in progress at this point.
# The old fetch tool couldn't handle this
result_of_retry_in_progress = """
{
  "cleanup_duration":0,
  "creator_user_name":"abc123-my-spn-abc123",
  "effective_performance_target":"PERFORMANCE_OPTIMIZED",
  "end_time":0,
  "execution_duration":0,
  "job_id":95377413594448,
  "job_run_id":1010765015110307,
  "number_in_job":1010765015110307,
  "run_duration":3129522,
  "run_id":1010765015110307,
  "run_name":"Testing Run",
  "run_page_url":"https://adb-customer-workspace.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/1010765015110307",
  "run_type":"SUBMIT_RUN",
  "setup_duration":0,
  "start_time":1772715481808,
  "state": {
    "life_cycle_state":"RUNNING",
    "state_message":"",
    "user_cancelled_or_timedout":false
  },
  "status": {
    "state":"RUNNING"
  },
  "tasks": [
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-0epqqpz4",
        "spark_context_id":"1165403962544971917"
      },
      "end_time":1772716947281,
      "execution_duration":904000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":527140997999428,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/527140997999428",
      "setup_duration":561000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job6",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481834,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job6"
    },
    {
      "attempt_number":0,
      "cleanup_duration":1000,
      "cluster_instance": {
        "cluster_id":"0305-125802-0wb0vh1c",
        "spark_context_id":"4301843509616872724"
      },
      "end_time":1772717472947,
      "execution_duration":1399000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":877507398122692,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/877507398122692",
      "setup_duration":591000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job4",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481834,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job4"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-d8of3aps",
        "spark_context_id":"4516930351231652"
      },
      "end_time":1772716752795,
      "execution_duration":739000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":8218917254448,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/8218917254448",
      "setup_duration":531000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job5",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481835,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job5"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "effective_performance_target":"PERFORMANCE_OPTIMIZED",
      "end_time":1772715628471,
      "environment_key":"tests_serverless_btb",
      "execution_duration":142000,
      "run_id":1110381068538260,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/1110381068538260",
      "setup_duration":4000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/serverless/btb",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481835,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_serverless_btb"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-yo0n2adc",
        "spark_context_id":"3089425300790311993"
      },
      "end_time":1772716835204,
      "execution_duration":822000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":1029085715023390,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/1029085715023390",
      "setup_duration":531000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job7",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481834,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job7"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-gc3a85j4",
        "spark_context_id":"6811963356110211031"
      },
      "end_time":1772716610342,
      "execution_duration":537000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":131588227550418,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/131588227550418",
      "setup_duration":591000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/finance",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481834,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"FAILED",
        "state_message":"Workload failed, see run output for details",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"RUN_EXECUTION_ERROR",
          "message":"Workload failed, see run output for details",
          "type":"CLIENT_ERROR"
        }
      },
      "task_key":"tests_cluster_finance"
    },
    {
      "attempt_number":1,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-155837-vkb43l00",
        "spark_context_id":"8963590389887219399"
      },
      "end_time":0,
      "execution_duration":0,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":902657498004028,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/902657498004028",
      "setup_duration":561000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/finance",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772726316416,
      "state": {
        "life_cycle_state":"RUNNING",
        "state_message":"In run",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"RUNNING"
      },
      "task_key":"tests_cluster_finance"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-759xee4g",
        "spark_context_id":"2855874866207624867"
      },
      "end_time":1772716840216,
      "execution_duration":827000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":473744681601415,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/473744681601415",
      "setup_duration":531000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job2",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481834,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job2"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-pto28mww",
        "spark_context_id":"2083828210166166616"
      },
      "end_time":1772717992313,
      "execution_duration":1919000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":711703946891630,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/711703946891630",
      "setup_duration":591000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job3",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481835,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job3"
    },
    {
      "attempt_number":0,
      "cleanup_duration":0,
      "cluster_instance": {
        "cluster_id":"0305-125802-60e0feo0",
        "spark_context_id":"3415202947221884357"
      },
      "end_time":1772717455688,
      "execution_duration":1472000,
      "libraries": [
        {
          "whl":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/libs/customer-1.0.241872-py3-none-any.whl"
        }
      ],
      "new_cluster": {
        "azure_attributes": {
          "availability":"ON_DEMAND_AZURE",
          "first_on_demand":1,
          "spot_bid_max_price":-1
        },
        "custom_tags": {
          "ResourceClass":"SingleNode"
        },
        "data_security_mode":"SINGLE_USER",
        "docker_image": {
          "basic_auth": {
            "password":"{{secrets/kv/Databricks--Registry--Password}}",
            "username":"warehouse"
          },
          "url":"clwhprodse.azurecr.io/warehouse:latest"
        },
        "driver_node_type_id":"Standard_E4d_v4",
        "enable_elastic_disk":true,
        "node_type_id":"Standard_E4d_v4",
        "num_workers":0,
        "runtime_engine":"STANDARD",
        "spark_conf": {
          "spark.databricks.cluster.profile":"singleNode",
          "spark.databricks.delta.preview.enabled":"true",
          "spark.databricks.delta.schema.autoMerge.enabled":"false",
          "spark.databricks.io.cache.enabled":"true",
          "spark.databricks.unityCatalog.volumes.enabled":"true",
          "spark.master":"local[*, 4]"
        },
        "spark_env_vars": {
          "PYSPARK_PYTHON":"/databricks/python3/bin/python3"
        },
        "spark_version":"16.4.x-scala2.12"
      },
      "run_id":173152087413362,
      "run_if":"ALL_SUCCESS",
      "run_page_url":"https://adb-123-example-123.5.azuredatabricks.net/?o=123-example-123#job/95377413594448/run/173152087413362",
      "setup_duration":501000,
      "spark_python_task": {
        "parameters": [
          "--basedir=/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793",
          "--folder=tests/cluster/job1",
          "--pytestargs=[\"--durations=0\"]"
        ],
        "python_file":"/Workspace/Users/abc123-my-spn-abc123/.spetlr/test/2026-03-05T12:57:58.779793/main.py"
      },
      "start_time":1772715481834,
      "state": {
        "life_cycle_state":"TERMINATED",
        "result_state":"SUCCESS",
        "state_message":"",
        "user_cancelled_or_timedout":false
      },
      "status": {
        "state":"TERMINATED",
        "termination_details": {
          "code":"SUCCESS",
          "message":"",
          "type":"SUCCESS"
        }
      },
      "task_key":"tests_cluster_job1"
    }
  ]
}
"""
