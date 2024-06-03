import os
import shutil
import sys
from typing import Any, Iterator, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs
from databricks.sdk.service.compute import InstancePoolAndStats


def _try_resolve(obj: Any, key: str):
    try:
        return obj[key]
    except (KeyError, TypeError):
        return obj


class DbCli:
    w: Optional[WorkspaceClient] = None

    @classmethod
    def get_client(cls) -> WorkspaceClient:
        if cls.w is None:
            cls.w = WorkspaceClient()
        return cls.w

    def whoami(self) -> str:
        return self.get_client().current_user.me().user_name

    def cancel_run(self, run_id: int) -> None:
        self.get_client().jobs.cancel_run(run_id)

    def get_run(self, run_id: int) -> jobs.Run:
        return self.get_client().jobs.get_run(run_id)

    def get_run_output(self, run_id: int) -> jobs.RunOutput:
        return self.get_client().jobs.get_run_output(run_id)

    def list_instance_pools(self) -> Iterator[InstancePoolAndStats]:
        return self.get_client().instance_pools.list()

    def submit(self, workflow: dict, dry_run=False) -> int:
        if dry_run:
            print("Action skipped for dry-run. Job not submitted.")
            print("You can find the json to be submitted in the staging area.")
            print("Dry run ends here.")
            sys.exit(0)

        return self.get_client().jobs._api.do(
            "POST", "/api/2.1/jobs/runs/submit", body=workflow
        )["run_id"]

    def execv_run_file(self, file_path: str, dry_run=False):
        databricks = shutil.which("databricks")
        if databricks is None:
            print("databricks not found in PATH.", file=sys.stderr)
            sys.exit(1)

        args = ["databricks", "jobs", "submit", f"--json=@{file_path}"]

        if dry_run:
            print("Action skipped for dry-run:")
            print(">>", *args)
            sys.exit(0)

        try:
            os.execv(databricks, args)
        except Exception as e:
            print(f"Failed to execute the command: {e}", file=sys.stderr)
            sys.exit(1)
