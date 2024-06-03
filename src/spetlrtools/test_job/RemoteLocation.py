import base64
import datetime
import shutil
from dataclasses import dataclass
from pathlib import Path, PosixPath
from tempfile import TemporaryDirectory
from typing.io import BinaryIO

from databricks.sdk import WorkspaceClient
from databricks.sdk.service import workspace

from spetlrtools.test_job.dbcli import DbCli


class StageArea:
    """
    The stage are is either a temp-dir which is cleaned after the run, or, if --dry-run is used,
    the stage area is a local folder whose contents can be inspected for debug purposes.

    In the stage area, the main.py, the libraries and the job.json are collected before submission
    of the job.
    """

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

    _dbwsc: WorkspaceClient

    date = datetime.datetime.now().isoformat()  # mockable as class member

    def __init__(self, stage_area: str):
        self.stage_area = Path(stage_area)
        self._dbwsc = DbCli().get_client()
        self.me = self._dbwsc.current_user.me().user_name
        self.remote_home_to_base = ""
        self.remote_home = PosixPath()

    def add_local_path(self, source: str, dir: str = None) -> str:
        """Add a source file to the target work area under a certain directory.
        The file is staged. Upload only happens at the end when we call .upload()"""
        source = Path(source)

        stage_dir = self.stage_area / self.remote_home_to_base
        if dir is None:
            target_part = Path(self.remote_home_to_base) / source.parts[-1]
        else:
            stage_dir = stage_dir / dir
            target_part = Path(self.remote_home_to_base) / dir / source.parts[-1]

        stage_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy(source, self.stage_area / target_part)
        return str(self.remote_home / target_part)

    @dataclass
    class FileRef:
        remote: str
        local: str

    def _mkdirs(self, path: str):
        """Depending on the selected remote, use the dbfs or the workspace api"""
        raise NotImplementedError()

    def _upload_object(self, path: str, f: BinaryIO):
        """Depending on the selected remote, use the dbfs or the workspace api"""
        raise NotImplementedError()

    def new_local_file(self, name: str) -> FileRef:
        """Add a new file to the target work area under a certain directory.
        The directory is made to exist. The file should be written to the local
        path which is the second return value.
        Upload only happens at the end when we call .upload()"""

        local_source = Path(self.stage_area) / self.remote_home_to_base / name
        local_source.parent.mkdir(exist_ok=True, parents=True)

        remote_target = self.remote_home / self.remote_home_to_base / name

        return self.FileRef(remote=str(remote_target), local=str(local_source))

    def remote_base(self) -> str:
        """The full path of the work area once it has been uploaded to databricks."""
        raise NotImplementedError()

    def upload(self, dry_run=False):
        """Upload the staging area to databricks, either under dbfs root or under the workspace home folder."""
        if dry_run:
            print("Not uploading test job folder - Action skipped for dry-run.")
        else:
            print("Now uploading test job folder")
            self._upload_dir(self.remote_home, self.stage_area)

    def _upload_dir(self, remote, local):
        """recursively upload directories and files."""
        for obj in Path(local).iterdir():
            if obj.is_dir():
                new_remote = f"{remote}/{obj.name}"
                new_local = str(obj)
                self._mkdirs(f"{remote}/{obj.name}")
                self._upload_dir(new_remote, new_local)
            else:
                with open(obj, "rb") as f:
                    self._upload_object(path=f"{remote}/{obj.name}", f=f)


class WorkspaceLocation(RemoteLocation):
    """Use the Workspace API for remote files."""

    def __init__(self, stage_area: str):
        super().__init__(stage_area)
        self.remote_home_to_base = f".spetlr/test/{self.date}"
        self.remote_home = PosixPath(f"/Workspace/Users/{self.me}")

    def remote_base(self) -> str:
        return str(self.remote_home / self.remote_home_to_base)

    def _mkdirs(self, path: str):
        self._dbwsc.workspace.mkdirs(path)

    def _upload_object(self, path: str, f: BinaryIO):
        content = base64.b64encode(f.read()).decode()
        self._dbwsc.workspace.import_(
            path=path, content=content, format=workspace.ImportFormat.AUTO
        )


class DbfsLocation(RemoteLocation):
    """Use the DBFS API for remote files."""

    def __init__(self, stage_area: str):
        super().__init__(stage_area)
        self.date = self.date.replace(":", ".")
        self.remote_home_to_base = f"spetlr/test/{self.me}/{self.date}"
        self.remote_home = PosixPath("dbfs:/")

    def remote_base(self) -> str:
        return str(self.remote_home / self.remote_home_to_base)

    def _mkdirs(self, path: str):
        self._dbwsc.dbfs.mkdirs(path)

    def _upload_object(self, path: str, f: BinaryIO):
        self._dbwsc.dbfs.upload(path=path, src=f)
