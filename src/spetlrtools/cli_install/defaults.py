"""
This script is designed for setting up environment-specific configurations for the Databricks CLI tool.
It contains functionality to:
- Detect the operating system of the user and determine if it is Windows.
- Define default target paths for the Databricks CLI executable based on the operating system.
- Store the GitHub repository URL of the Databricks CLI for reference or further use.

The script uses the 'platform' and 'sysconfig' modules to accurately identify the environment and
set file paths, ensuring compatibility with different operating systems, particularly Windows and Unix-based systems.
"""

import platform
import re
import sysconfig
from pathlib import Path


def isWin():
    return bool(re.match(".*windows.*", platform.system(), flags=re.IGNORECASE))


_DEFAULT_TARGET = Path(sysconfig.get_paths()["scripts"]) / (
    "databricks.exe" if isWin() else "databricks"
)
_DATABRICKS_CLI_REPO = "https://github.com/databricks/cli"
