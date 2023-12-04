import json
import re
import subprocess
import sys


class DbCli:
    def __init__(self):
        # establish databricks cli versrion
        try:
            version_string = subprocess.check_output(
                ["databricks", "--version"], encoding="utf-8"
            )
        except FileNotFoundError:
            # in case of missing executable, assume v1
            version_string = "Databricks CLI v0.210.1"
        match = re.match(r".*[^.0-9](\d+)\.(\d+)\.(\d+).*", version_string)
        version_tuple = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if version_tuple < (0, 19, 0):
            self.version = 1
        else:
            self.version = 2

        if self.version == 1:
            self.dbjcall("jobs configure --version=2.1")

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

    def cancel_run(self, run_id: int):
        if self.version == 1:
            return self.dbcall(f"runs cancel --run-id {run_id}")
        else:
            return self.dbcall(f"jobs cancel_run {run_id}")

    def get_run(self, run_id: int):
        if self.version == 1:
            return self.dbjcall(f"runs get --run-id {run_id}")
        else:
            return self.dbjcall(f"jobs get-run {run_id}")

    def list_instance_pools(self):
        if self.version == 1:
            return self.dbjcall("instance-pools list --output JSON")["instance_pools"]
        else:
            return self.dbjcall("instance-pools list --output JSON")

    def submit_run_file(self, file_path: str):
        if self.version == 1:
            return self.dbjcall(f"runs submit --json-file {file_path}")
        else:
            return self.dbjcall(f"jobs submit --no-wait --json @{file_path}")


dbcli = DbCli()
