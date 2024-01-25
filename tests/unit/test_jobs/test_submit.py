import unittest
from unittest.mock import patch

from spetlrtools.test_job.submit import DbTestFolder, PoolBoy


class TestSubmit(unittest.TestCase):
    @patch("spetlrtools.test_job.dbcli.DbCli.check_connection")
    @patch("spetlrtools.test_job.submit.dbcli.dbcall")
    def test_dbtestfolder_enter_exit(self, mock_dbcall, mock_check_connection):
        # Mock the necessary functions and objects
        mock_dbcall.return_value = None
        mock_check_connection.return_value = None

        with DbTestFolder() as test_folder:
            # Ensure the test folder is created correctly
            print(test_folder.remote)
            self.assertTrue(test_folder.remote.startswith("dbfs"))
            self.assertTrue(len(test_folder.remote) > len("/test/"))
            # self.assertTrue(test_folder.remote.endswith("/"))

            # Mock the dbcli.dbcall function to simulate successful directory creation
            mock_dbcall.assert_called_with(f"fs mkdirs {test_folder.remote}")
            mock_dbcall.reset_mock()  # Reset the mock for the exit check

        # Ensure the test folder is deleted after exiting the context manager
        # mock_dbcall.assert_called_with(f"fs rm -r {test_folder.remote}")

    @patch("spetlrtools.test_job.submit.dbcli.dbcall")
    def test_poolboy_lookup(self, mock_dbcall):
        # Mock the necessary functions and objects
        mock_dbcall.return_value = '{"instance_pools": [{"instance_pool_name": "my_instance_pool", "instance_pool_id": "123456"}]}'

        poolboy = PoolBoy()

        # If you search for a poolid - you will just get it back
        self.assertEqual(poolboy.lookup("foobar"), "foobar")

        # If you search for a non-existing poolname with the marker - you get exeption
        with self.assertRaises(KeyError):
            self.assertEqual(
                poolboy.lookup("instance-pool://foobar"), "instance-pool://foobar"
            )

        # If you search for a existing poolname with the marker - you get the id
        self.assertEqual(poolboy.lookup("instance-pool://my_instance_pool"), "123456")

    @patch("spetlrtools.test_job.submit.dbcli.list_instance_pools")
    def test_poolboy_get_instance_pools(self, mock_list_instance_pools):
        # Mock the list_instance_pools function
        mock_response = [
            {"instance_pool_name": "pool1", "instance_pool_id": "instance-pool://1"},
            {"instance_pool_name": "pool2", "instance_pool_id": "instance-pool://2"},
        ]
        mock_list_instance_pools.return_value = mock_response

        poolboy = PoolBoy()

        # Ensure the instance pools are fetched correctly
        expected_lookup = {"pool1": "instance-pool://1", "pool2": "instance-pool://2"}
        self.assertEqual(poolboy._lookup, expected_lookup)


if __name__ == "__main__":
    unittest.main()
