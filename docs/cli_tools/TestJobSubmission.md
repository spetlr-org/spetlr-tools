
# Test Job submission

The command `spetlr-test-job` can be used to run unit-test on a databricks cluster.
The command can submit a single job run, but additionally:

 - your unittests folder is archived and sent to databricks so that tests can be run 
   on a cluster
 - a main script is automatically pushed to databricks, so you don't have to supply 
   your own
 - At a specified level below your total tests-folder, the job is split into parallel 
   tasks
 - Test output is collected by using the cluster log functionality of databricks
 - a fetch command can return all stdout

## How to submit

Usage:
```powershell
usage: spetlr-test-job submit [-h] [--wheels WHEELS] --tests TESTS (--task TASK | --tasks-from TASKS_FROM) (--cluster CLUSTER | --cluster-file CLUSTER_FILE)
                           [--sparklibs SPARKLIBS | --sparklibs-file SPARKLIBS_FILE] [--requirement REQUIREMENT | --requirements-file REQUIREMENTS_FILE] [--main-script MAIN_SCRIPT]    
                           [--pytest-args PYTEST_ARGS] [--out-json OUT_JSON]

Run Test Cases on databricks cluster.

optional arguments:
  -h, --help            show this help message and exit
  --wheels WHEELS       The glob paths of all wheels under test.
  --tests TESTS         Location of the tests folder. Will be sendt to databricks as a whole.
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
```

```powershell
spetlr-test-job submit `
    --tests tests `
    --tasks-from tests/cluster/job4 `
    --cluster-file cluster.json `
    --requirements-file requirements.txt `
    --sparklibs-file sparklibs.json `
    --out-json test.json
```

- `tests/` should be the folder containing all your tests. In the test run, you will 
  be able to reference it from the local folder `import tests.my.tool`
- `cluster/job4` will be the part of the test library from which tests will be 
  executed. In this example, the folder `tests/cluster/job4` exists. Its sub-folders 
  will be executed in one task per subfolder inside the test job.
- `cluster.json` should contain a cluster description for a job. Example
```json
{
  "spark_version": "9.1.x-scala2.12",
  "spark_conf": {
    "spark.databricks.cluster.profile": "singleNode",
    "spark.master": "local[*, 4]",
    "spark.databricks.delta.preview.enabled": true,
    "spark.databricks.io.cache.enabled":true
  },
  "azure_attributes": {
    "availability": "ON_DEMAND_AZURE",
    "first_on_demand": 1,
    "spot_bid_max_price": -1
  },
  "node_type_id": "Standard_DS3_v2",
  "custom_tags": {
    "ResourceClass":"SingleNode"
  },
  "spark_env_vars": {
    "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
  },
  "num_workers": 0
}
```
- the optional `requirements.txt` should contain a pip-style list of requirements
- the optional `sparklibs.json` should contain spark dependencies as an array. Example:
```json
[
    {
        "maven": {
            "coordinates": "com.microsoft.azure:spark-mssql-connector_2.12:1.2.0"
        }
    }
]
```
- optionally, the run ID is written to `test.json` so that it does not have to be 
  provided on the command line when fetching.

## How to fetch
Usage:
```powershell
usage: spetlr-test-job fetch [-h] (--runid RUNID | --runid-json RUNID_JSON) [--stdout STDOUT] [--failfast]

Return test run result.

optional arguments:
  -h, --help            show this help message and exit
  --runid RUNID         Run ID of the test job
  --runid-json RUNID_JSON
                        File with JSON document describing the Run ID of the test job.
  --stdout STDOUT       Output test stdout to this file.
  --failfast            Stop and cancel job on first failed task.
```

The `fetch` operation consists of the following steps:
- periodically query the job progress and print updates to the console.
- if any task completes, the stdout file is downloaded
- if `failfast` is selected, a single failed task will result in a cancelling of the 
  overall job.
- If the job succeeds, the command will return with 0 return value, making it 
  suitable for use in test pipelines.

Example fetch:
```powershell
spetlr-test-job fetch --runid-json .\test.json --stdout .\stdout.txt
```

- The run ID can be supplied through a file or directly in the command line.
- if `stdout` is set, the output will be written to this file instead of printing to 
  the console.