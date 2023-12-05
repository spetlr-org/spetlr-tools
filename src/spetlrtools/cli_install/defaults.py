import platform
import re
import sysconfig
from pathlib import Path


def isWin():
    return bool(re.match(".*windows.*", platform.system()))


_DEFAULT_TARGET = Path(sysconfig.get_paths()["scripts"]) / (
    "databricks.exe" if isWin() else "databricks"
)
_DATABRICKS_CLI_REPO = "https://github.com/databricks/cli"
