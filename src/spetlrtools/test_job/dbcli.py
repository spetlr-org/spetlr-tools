import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any


def _try_resolve(obj: Any, key: str):
    try:
        return obj[key]
    except (KeyError, TypeError):
        return obj


class DbCli:
    def __init__(self):
        # establish databricks cli version
        error = Exception(
            "databricks cli v2 must be installed. "
            'You can get it by running "spetlr-databricks-cli install"'
        )
        try:
            version_string = subprocess.check_output(
                ["databricks", "--version"], encoding="utf-8"
            )
        except FileNotFoundError:
            raise error
        match = re.match(r".*[^.0-9](\d+)\.(\d+)\.(\d+).*", version_string)
        version_tuple = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if version_tuple < (0, 19, 0):
            raise error

    def dbjcall(self, command: str):
        """Run the command line "databricks "+command and return the unpacked json string."""
        res = self.dbcall(command)
        try:
            if res:
                return json.loads(res)
            else:
                return None
        except:  # noqa OK because we re-raise
            print(res)
            raise

    def check_connection(self):
        try:
            self.dbjcall("clusters list  --output=JSON")
        except subprocess.CalledProcessError:
            print(
                "Could not query databricks state. Is your token up to date?",
                file=sys.stderr,
            )
            exit(-1)

    def dbcall(self, command: str):
        """Run the command line "databricks "+command and return the resulting string."""
        p = subprocess.run(
            "databricks " + command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        return p.stdout

    def whoami(self) -> str:
        return self.dbjcall("current-user me")["userName"]

    def cancel_run(self, run_id: int):
        return self.dbcall(f"jobs cancel_run {run_id}")

    def get_run(self, run_id: int):
        return self.dbjcall(f"jobs get-run {run_id}")

    def list_instance_pools(self):
        return (
            _try_resolve(
                self.dbjcall("instance-pools list --output JSON"), "instance_pools"
            )
            or []
        )

    def submit_run_file(self, file_path: str):
        return self.dbjcall(f"jobs submit --no-wait --json @{file_path}")

    def execv_run_file(self, file_path: str):
        databricks = shutil.which("databricks")
        if databricks is None:
            print("databricks not found in PATH.", file=sys.stderr)
            sys.exit(1)

        try:
            os.execv(
                databricks, ["databricks", "jobs", "submit", f"--json=@{file_path}"]
            )
        except Exception as e:
            print(f"Failed to execute the command: {e}", file=sys.stderr)
            sys.exit(1)
