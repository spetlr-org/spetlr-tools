import unittest

import pyspark.sql.types as T
from spetlr.utils import DataframeCreator

from spetlrtools.testing import DataframeTestCase, TestHandle


class ExtractTestHandle(DataframeTestCase):
    df_test_data = [("test",)]

    test_schema = T.StructType([T.StructField("value", T.StringType(), True)])

    df_test = DataframeCreator.make(
        schema=test_schema,
        data=df_test_data,
    )

    def test_01_read(self):
        td = TestHandle(provides=self.df_test)

        df_read = td.read()

        self.assertDataframeMatches(
            df=df_read,
            expected_data=self.df_test_data,
        )

    def test_02_read_exception(self):
        td = TestHandle()

        with self.assertRaises(AssertionError):
            td.read()

    def test_03_get_schema(self):
        td = TestHandle(schema=self.test_schema)

        schema = td.get_schema()

        self.assertEqualSchema(self.test_schema, schema)

    def test_04_get_schema_from_df(self):
        td = TestHandle(provides=self.df_test)

        schema = td.get_schema()

        self.assertEqualSchema(self.test_schema, schema)

    def test_05_get_schema_exception(self):
        td = TestHandle()

        with self.assertRaises(AssertionError):
            td.read()


if __name__ == "__main__":
    unittest.main()
