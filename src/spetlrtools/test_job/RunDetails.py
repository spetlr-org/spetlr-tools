import re
import subprocess
import tempfile
import time
from pathlib import PosixPath

from spetlrtools.test_job import test_main
from spetlrtools.test_job.dbcli import dbcli


class DbfsFileDoesNotExist(Exception):
    pass


class RunDetails:
    """Object representing the details of a job run"""

    details: dict

    def __init__(self, run_id: int):
        self.run_id = run_id
        self.refresh()
        print(f"Job details: {self.details['run_page_url']}")

    def refresh(self):
        """refresh the internal details by querying databricks"""
        self.details = dbcli.get_run(self.run_id)

    def cancel(self):
        """Cancel the run on databricks."""
        dbcli.cancel_run(self.run_id)

    def get_stdout(self, task_key: str) -> str:
        """Return the driver stdout from the cluster logs."""
        print(f"Getting stdout for {task_key}")
        (task,) = [t for t in self.details["tasks"] if t["task_key"] == task_key]
        log_destination = task["new_cluster"]["cluster_log_conf"]["dbfs"]["destination"]
        cluster_instance = task["cluster_instance"]["cluster_id"]
        print(log_destination, cluster_instance)
        log_stout_path = f"{log_destination}/{cluster_instance}/driver/stdout"
        with tempfile.TemporaryDirectory() as tmp:
            try:
                self.wait_until_exists(log_stout_path)
            except DbfsFileDoesNotExist:
                return f"-=ERROR FETCHING LOG FILES FROM  {log_stout_path}=-"

            dbcli.dbcall(f"fs cp {log_stout_path} {tmp}/stdout")
            with open(f"{tmp}/stdout", encoding="utf-8") as f:
                return clean_cluster_output(f.read())

    def wait_until_exists(self, location: str, tries=20, sleep_s=1):
        """Wait until the file exists on dbfs."""
        # sometimes cluster logs do not appear immediately.
        # TODO: expose the wait parameters on the cli
        p = PosixPath(location)
        for i in range(tries):
            time.sleep(sleep_s)

            try:
                parts = [
                    s.strip()
                    for s in dbcli.dbcall(f"fs ls {str(p.parent)}").splitlines()
                ]
            except subprocess.CalledProcessError:
                continue

            if p.name in parts:
                return

        raise DbfsFileDoesNotExist()


def clean_cluster_output(raw_stdout: str) -> str:
    """
    Clean in two steps:
    - Step 1 is to find the sequence of invisible marker characters
      and discard everything before that.
    - Step 2 is to use regexp to get rid of interspersed java warnings.
    """
    # Step 1 split on marker
    try:
        _, raw_stdout = raw_stdout.split(test_main.marker)
    except ValueError:
        # no marker in input?! try moving on regardless
        pass

    # step 2 remove GC warnings
    timestamp = (
        r"\d{4}-\d{2}-\d{2}"  # Year, month, day
        r"T\d{2}:\d{2}:\d{2}"  # Hour, minute, second
        r"\.\d{3}"  # millseconds
        r"\d*"  # further fractional seconds
        r"(\+\d+|-\d+|Z)"  # Time zone info
    )
    pattern = (
        r"^"  # preceeded by a newline or start of string
        f"({timestamp}:? )+"  # At least 1 timestamp followed by ": "
        r"(\d+\.\d+: )?"  # unknown indicator
        r"\["  # any block starting with a [
        r".+$[\r\n]*"  # everything to end of line and all following newlines
    ).replace(" ", r"\s*")

    pat = re.compile(pattern, flags=re.MULTILINE)

    return pat.sub("", raw_stdout)
