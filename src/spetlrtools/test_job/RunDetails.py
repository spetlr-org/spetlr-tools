from databricks.sdk.service import jobs

from spetlrtools.test_job.dbcli import DbCli


class RunDetails:
    """Object representing the details of a job run"""

    details: jobs.Run

    def __init__(self, run_id: int):
        self.run_id = run_id
        self._db = DbCli()
        self.refresh()
        print(f"Job details: {self.details.run_page_url}")

    def refresh(self):
        """refresh the internal details by querying databricks"""
        self.details = self._db.get_run(self.run_id)

    def cancel(self):
        """Cancel the run on databricks."""
        self._db.cancel_run(self.run_id)

    def get_stdout(self, task_key: str) -> str:
        """Return the driver stdout from the cluster logs."""
        self.refresh()

        print(f"Getting stdout for {task_key}")
        task: jobs.RunTask

        # get latest attempt for all tasks of this key
        # this allows fetch to succeed in case a "repair" fixed a transient task failure
        tasks_for_key = (t for t in self.details.tasks if t.task_key == task_key)
        # sort by negative attempt number
        task = sorted(tasks_for_key,key=lambda t:-t.attempt_number)[0]

        task_id = task.run_id
        output = self._db.get_run_output(task_id)
        return output.logs
