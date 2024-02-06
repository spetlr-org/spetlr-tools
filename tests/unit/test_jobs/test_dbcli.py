import subprocess
import unittest
from unittest.mock import MagicMock, patch

from spetlrtools.test_job.dbcli import DbCli


class TestDbCli(unittest.TestCase):
    """
    Test the DbCli class from dbcli.py
    """

    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_dbjcall_returns_correct_output(self, mock_run, mock_check_output):
        """
        Test dbjcall method returns the correct output
        """
        # Mocking the subprocess.check_output in __init__
        mock_check_output.return_value = "Databricks CLI Version: 0.10.0"

        # Mocking subprocess.run used in dbcall method
        # Setting stdout to a JSON string that is expected in __init__ method of DbCli
        mock_run.return_value = MagicMock(returncode=0, stdout='{"result": "success"}')

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Setting up the return value for the dbjcall method call with "databricks jobs list"
        mock_run.return_value.stdout = '{"jobs": ["Job1", "Job2", "Job3"]}'

        # Call the dbjcall method with the example command
        result = dbcli_instance.dbjcall("databricks jobs list")

        # Check if the result is as expected
        expected_result = {"jobs": ["Job1", "Job2", "Job3"]}
        self.assertEqual(result, expected_result)

    @patch("subprocess.run")
    @patch("sys.exit")
    def test_check_connection_success(self, mock_exit, mock_run):
        """
        Test check_connection method succeeds without raising an error
        """
        # Mock subprocess.run to return a valid version string for the version check in __init__
        mock_run.return_value = MagicMock(returncode=0, stdout='{"version": "0.10.0"}')

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Setting subprocess.run mock for the check_connection call
        mock_run.return_value = MagicMock(returncode=0, stdout="{}")

        # Call the check_connection method and expect no system exit
        dbcli_instance.check_connection()
        mock_exit.assert_not_called()

    @patch("subprocess.run")
    def test_check_connection_failure(self, mock_run):
        """
        Test check_connection method fails and raises SystemExit
        """
        # Mock subprocess.run for the version check in __init__
        mock_run.return_value = MagicMock(returncode=0, stdout='{"version": "0.10.0"}')

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Mock subprocess.run to raise CalledProcessError for the check_connection call
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "clusters list  --output=JSON"
        )

        # Call the check_connection method and expect SystemExit to be raised
        with self.assertRaises(SystemExit) as cm:
            dbcli_instance.check_connection()

        # Check that the exit code is -1
        self.assertEqual(cm.exception.code, -1)

    @patch("subprocess.run")
    def test_cancel_run(self, mock_run):
        """
        Test cancel_run method for both versions
        """
        # Mock subprocess.run to return a valid version string for the version check in __init__
        mock_run.return_value = MagicMock(returncode=0, stdout='{"version": "0.10.0"}')

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Test for version 1
        dbcli_instance.version = 1
        dbcli_instance.cancel_run(run_id=123)
        mock_run.assert_called_with(
            "databricks runs cancel --run-id 123",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )

        # Reset the mock
        mock_run.reset_mock()

        # Test for version 2
        dbcli_instance.version = 2
        dbcli_instance.cancel_run(run_id=123)
        mock_run.assert_called_with(
            "databricks jobs cancel_run 123",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )

    @patch("subprocess.run")
    @patch("subprocess.check_output")
    def test_get_run(self, mock_check_output, mock_run):
        """
        Test get_run method for both versions
        """
        # Mock subprocess.check_output for the version check in __init__
        mock_check_output.return_value = "Databricks CLI Version: 0.10.0"

        # Mock subprocess.run to return a JSON string for the get_run command
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"run_id": 123, "state": "RUNNING"}'
        )

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Test for version 1
        dbcli_instance.version = 1
        result_v1 = dbcli_instance.get_run(run_id=123)
        mock_run.assert_called_with(
            "databricks runs get --run-id 123",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        expected_result_v1 = {"run_id": 123, "state": "RUNNING"}
        self.assertEqual(result_v1, expected_result_v1)

        # Reset the mock
        mock_run.reset_mock()

        # Test for version 2
        dbcli_instance.version = 2
        result_v2 = dbcli_instance.get_run(run_id=123)
        mock_run.assert_called_with(
            "databricks jobs get-run 123",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        expected_result_v2 = {"run_id": 123, "state": "RUNNING"}
        self.assertEqual(result_v2, expected_result_v2)

    @patch("subprocess.run")
    @patch("subprocess.check_output")
    def test_list_instance_pools_with_key(self, mock_check_output, mock_run):
        """
        Test list_instance_pools method when instance_pools key is present
        """
        # Mock subprocess.check_output for the version check in __init__
        mock_check_output.return_value = "Databricks CLI Version: 0.10.0"

        # Mock subprocess.run to return a JSON string with the instance_pools key
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"instance_pools": [{"pool_id": "pool1"}, {"pool_id": "pool2"}]}',
        )

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Call list_instance_pools method
        result = dbcli_instance.list_instance_pools()

        # Expected result
        expected_result = [{"pool_id": "pool1"}, {"pool_id": "pool2"}]
        self.assertEqual(result, expected_result)

    @patch("subprocess.run")
    @patch("subprocess.check_output")
    def test_list_instance_pools_without_key(self, mock_check_output, mock_run):
        """
        Test list_instance_pools method when instance_pools key is not present
        """
        # Mock subprocess.check_output for the version check in __init__
        mock_check_output.return_value = "Databricks CLI Version: 0.10.0"

        # Mock subprocess.run to return a JSON string without the instance_pools key
        mock_run.return_value = MagicMock(returncode=0, stdout='{"other_key": "value"}')

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Call list_instance_pools method
        result = dbcli_instance.list_instance_pools()

        # Expected result
        expected_result = {
            "other_key": "value"
        }  # Since the "instance_pools" key is not present, the dict is returned
        self.assertEqual(result, expected_result)

    @patch("subprocess.run")
    @patch("subprocess.check_output")
    def test_list_instance_pools_no_pool(self, mock_check_output, mock_run):
        """
        Test list_instance_pools method when instance_pools key is not present
        """
        # Mock subprocess.check_output for the version check in __init__
        mock_check_output.return_value = "Databricks CLI Version: 0.10.0"

        # Mock subprocess.run to return a JSON string without the instance_pools key
        mock_run.return_value = MagicMock(returncode=0, stdout=None)

        # Create an instance of the DbCli class
        dbcli_instance = DbCli()

        # Call list_instance_pools method
        result = dbcli_instance.list_instance_pools()

        # Expected result
        expected_result = (
            []
        )  # Since the "instance_pools" key is not present, the dict is returned
        self.assertEqual(result, expected_result)

    @patch("subprocess.run")
    def test_submit_run_file(self, mock_run):
        """
        Test submit_run_file method for both versions
        """
        # Mock subprocess.run to simulate a successful run submission
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"run_id": 123, "state": "RUNNING"}'
        )

        # Mock subprocess.check_output for the version check in __init__
        mock_version_string = "Databricks CLI Version: 0.10.0"
        with patch("subprocess.check_output", return_value=mock_version_string):
            # Create an instance of the DbCli class
            dbcli_instance = DbCli()

        # Mock the version to be v2
        dbcli_instance.version = 2

        # Call submit_run_file method with a file path
        file_path = "/path/to/your/file.json"
        result = dbcli_instance.submit_run_file(file_path)

        # Expected result for v2
        expected_result_v2 = dbcli_instance.dbjcall(
            f"jobs submit --no-wait --json @{file_path}"
        )

        # Assert that the method returns the expected result for v2
        self.assertEqual(result, expected_result_v2)

        # Mock the version to be v1
        dbcli_instance.version = 1

        # Call submit_run_file method with a file path
        result = dbcli_instance.submit_run_file(file_path)

        # Expected result for v1
        expected_result_v1 = dbcli_instance.dbjcall(
            f"runs submit --json-file {file_path}"
        )

        # Assert that the method returns the expected result for v1
        self.assertEqual(result, expected_result_v1)


if __name__ == "__main__":
    unittest.main()
