import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from spetlrtools.spetlr_db_connect.spetlr_db_connect import (
    main,
)
from spetlrtools.spetlr_db_connect.spetlr_db_connect_utils_posix import (
    set_user_env_var_posix,
)
from spetlrtools.spetlr_db_connect.spetlr_db_connect_utils_win import (
    set_user_env_var_windows,
)

# On Linux there's no winreg—create a dummy module so that patch("winreg.…") works
if "winreg" not in sys.modules:
    sys.modules["winreg"] = types.ModuleType("winreg")


class DummyKey:
    """
    Dummy implementation of a Winreg key to capture SetValueEx and Close calls.
    """

    def __init__(self):
        self.values = {}

    def SetValueEx(self, name, reserved, type, value):
        self.values[name] = value

    def Close(self):
        pass


class DummyRegistry:
    """
    Dummy registry that returns DummyKey instances for OpenKey calls.
    """

    def __init__(self):
        self.keys = {}

    def OpenKey(self, root, path, reserved, access):
        key = DummyKey()
        self.keys[path] = key
        return key


class TestSpetlrDbConnect(unittest.TestCase):
    """
    Test suite for spetlr-dbconnect-cli:
    - Verifies Windows and POSIX environment variable setters
    - Validates CLI main behavior on Linux (POSIX) and Windows platforms
    """

    def setUp(self):
        """
        Patch out winreg calls, environment setters, and subprocess.run
        to capture interactions without side effects.
        """
        # Patch winreg for Windows-variable setting
        self.dummy = DummyRegistry()
        self.win_patches = [
            patch("winreg.OpenKey", new=self.dummy.OpenKey),
            patch(
                "winreg.SetValueEx",
                new=lambda key, name, res, typ, val: key.SetValueEx(
                    name, res, typ, val
                ),
            ),
            patch("winreg.CloseKey", new=lambda key: key.Close()),
            patch("winreg.HKEY_CURRENT_USER", new=object()),
            patch("winreg.KEY_SET_VALUE", new=0x0002),
            patch("winreg.REG_EXPAND_SZ", new=1),
        ]
        for p in self.win_patches:
            p.start()

        # Stub environment setters to capture calls
        self.env_windows_calls = []
        self.env_posix_calls = []
        self.p_env_win = patch(
            "spetlrtools.spetlr_db_connect.spetlr_db_connect.set_user_env_var_windows",
            new=lambda name, val: self.env_windows_calls.append((name, val)),
        )
        self.p_env_pos = patch(
            "spetlrtools.spetlr_db_connect.spetlr_db_connect.set_user_env_var_posix",
            new=lambda name, val: self.env_posix_calls.append((name, val)),
        )
        self.p_env_win.start()
        self.p_env_pos.start()

        # Stub subprocess.run to capture CLI calls
        self.subproc_calls = []
        self.p_run = patch(
            "spetlrtools.spetlr_db_connect.spetlr_db_connect.subprocess.run",
            new=lambda cmd, check=False: self.subproc_calls.append(cmd)
            or type("R", (object,), {"returncode": 0})(),
        )
        self.p_run.start()

    def tearDown(self):
        """
        Stop all active patches.
        """
        for p in self.win_patches + [self.p_env_win, self.p_env_pos, self.p_run]:
            p.stop()

    def test_set_user_env_var_windows_simple(self):
        """
        Test that set_user_env_var_windows writes the correct key/value
        pair into the dummy Windows registry.
        """
        set_user_env_var_windows("TEST_VAR", "TEST")
        key = self.dummy.keys.get("Environment")
        self.assertIsNotNone(key, "Registry key 'Environment' was not opened")
        self.assertEqual(
            key.values["TEST_VAR"], "TEST", "Value was not set correctly in registry"
        )

    def test_set_user_env_var_posix_simple(self):
        """
        Test that set_user_env_var_posix appends the correct export
        line and marker comment to ~/.bashrc.
        """
        tmp_home = tempfile.mkdtemp()
        os.environ["HOME"] = tmp_home
        os.environ["USERPROFILE"] = tmp_home
        os.environ["SHELL"] = "/bin/bash"
        rc = os.path.join(tmp_home, ".bashrc")
        with open(rc, "w") as f:
            f.write("# existing")

        set_user_env_var_posix("FOO", "BAR")
        with open(rc, "r") as f:
            content = f.read()
        self.assertIn(
            "# Added by spetlr-dbconnect-cli",
            content,
            "Marker comment not found in rc file",
        )
        self.assertIn("export FOO=BAR", content, "Export line not added to rc file")

    def test_main_cli_linux(self):
        """
        Simulate running the CLI on a Linux system: it should call
        the POSIX setter functions in the correct order and then
        invoke the Databricks CLI commands.
        """
        with patch(
            "spetlrtools.spetlr_db_connect.spetlr_db_connect.platform.system",
            return_value="Linux",
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--profile-name", "prof", "--host-url", "host", "--disable-connect"],
                prog_name="spetlr-dbconnect-cli",
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            self.env_posix_calls,
            [
                ("SPETLR_DATABRICKS_CONNECT", "false"),
                ("DATABRICKS_CONFIG_PROFILE", "prof"),
                ("DATABRICKS_HOST", "host"),
            ],
            "POSIX setter calls did not match expected sequence",
        )
        expected_login = [
            "databricks",
            "auth",
            "login",
            "--configure-cluster",
            "--profile",
            "prof",
            "--host",
            "host",
        ]
        expected_env = ["databricks", "auth", "env", "--profile", "prof"]
        self.assertEqual(
            self.subproc_calls,
            [expected_login, expected_env],
            "Databricks CLI commands not called as expected",
        )

    def test_main_cli_windows(self):
        """
        Simulate running the CLI on Windows: it should call
        the Windows setter functions in the correct order and then
        invoke the Databricks CLI commands.
        """
        with patch(
            "spetlrtools.spetlr_db_connect.spetlr_db_connect.platform.system",
            return_value="Windows",
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--profile-name", "wp", "--host-url", "h"],
                prog_name="spetlr-dbconnect-cli",
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            self.env_windows_calls,
            [
                ("SPETLR_DATABRICKS_CONNECT", "false"),
                ("DATABRICKS_CONFIG_PROFILE", "wp"),
                ("DATABRICKS_HOST", "h"),
            ],
            "Windows setter calls did not match expected sequence",
        )
        expected_login = [
            "databricks",
            "auth",
            "login",
            "--configure-cluster",
            "--profile",
            "wp",
            "--host",
            "h",
        ]
        expected_env = ["databricks", "auth", "env", "--profile", "wp"]
        self.assertEqual(
            self.subproc_calls,
            [expected_login, expected_env],
            "Databricks CLI commands not called as expected",
        )


if __name__ == "__main__":
    unittest.main()
