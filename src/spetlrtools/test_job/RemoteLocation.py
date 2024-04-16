import datetime
import shutil
from pathlib import Path, PosixPath
from tempfile import TemporaryDirectory

from spetlrtools.test_job.dbcli import DbCli


class StageArea:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self._tmpdir = None

    def __enter__(self) -> str:
        if self.dry_run:
            self._stage_area = "./spetlr-test-job-working-area"
            print(f"Working in static stage area {self._stage_area}.")
            Path(self._stage_area).mkdir(parents=True, exist_ok=False)
            return self._stage_area
        else:
            self._tmpdir = TemporaryDirectory()
            return self._tmpdir.__enter__()

    def __exit__(self, exc_type, exc_val, traceback):
        if self.dry_run:
            print(f"Remember to delete the stage area {self._stage_area}.")
        else:
            return self._tmpdir.__exit__(exc_type, exc_val, traceback)


class RemoteLocation:
    """This class has two functions:
    - decide on a name for the remote location where we upload all the job details
    - present the databricks-internal path to that location
    - execute the upload
    """

    def upload(self):
        raise NotImplementedError()

    def add_local_path(self, source: str, dir: str = None) -> str:
        """Add a source file to the target work area under a certain directory.
        The file is staged. Upload only happens at the end when we call .upload()"""
        raise NotImplementedError()

    def remote_base(self) -> str:
        """The full path of the work area once it has been uploaded to databricks."""
        raise NotImplementedError()


class WorkspaceLocation(RemoteLocation):
    def __init__(self, stage_area: str):
        self.stage_area = stage_area
        self._dbcli = DbCli()
        self.me = self._dbcli.whoami()
        self.date = datetime.datetime.now().isoformat()
        self.remote_home_to_base = f".spetlr/test/{self.date}"
        self.remote_home = f"/Workspace/Users/{DbCli().whoami()}"

    def add_local_path(self, source: str, dir: str = None) -> str:
        source = Path(source)

        if dir is None:
            target_part = Path(self.remote_home_to_base) / source.parts[-1]
        else:
            stage_dir = Path(self.stage_area) / self.remote_home_to_base / dir
            stage_dir.mkdir(parents=True, exist_ok=True)

            target_part = Path(self.remote_home_to_base) / dir / source.parts[-1]

        shutil.copy(source, Path(self.stage_area) / target_part)
        return f"{self.remote_home}/{PosixPath(target_part)}"

    def remote_base(self) -> str:
        return f"{self.remote_home}/{self.remote_home_to_base}"

    def upload(self):
        print("Now uploading test job folder")
        self._dbcli.dbcall(f"workspace import-dir {self.stage_area} {self.remote_home}")
