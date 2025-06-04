import json

import pyspark.sql.functions as f
import pyspark.sql.types as t
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.types import StructType


class ExtractEncodedBodyUC:
    """
    Utility class to extract and parse JSON bodies from a binary encoded column
    This can be used for investigating eventhub data.

    Attributes:
        json_field (str): Name of the column containing JSON strings to be parsed.
        new_field_w_extracted_body (str): Name of the column to store parsed JSON as a StructType.
        _data_limit (int or None): Maximum number of rows to sample when inferring JSON schema.
    """

    def __init__(
        self,
        json_field: str = "Body",
        new_column_w_extracted_body: str = None,
        data_limit: int = None,
    ):
        self.json_field = json_field
        self.new_field_w_extracted_body = new_column_w_extracted_body or json_field
        self._data_limit = data_limit
        self._fields_have_same_name = self.json_field == self.new_field_w_extracted_body

    def extract_schema(self, df: DataFrame) -> StructType:
        """
        Infer and return the StructType schema of the JSON column.

        Args:
            df (DataFrame): Input DataFrame.

        Returns:
            StructType: Schema of the parsed JSON field.

        Raises:
            AssertionError: If `json_field` not in DataFrame.
        """
        assert self.json_field in df.columns, "The body column is not in the dataframe"

        total_schema = self.transform_df(df).schema

        return StructType([total_schema[self.new_field_w_extracted_body]])

    def extract_schema_as_json(self, df: DataFrame, pretty_json: bool = False) -> str:
        """
        Return the JSON schema of the parsed field as a string.

        Args:
            df (DataFrame): Input DataFrame.
            pretty_json (bool): If True, format with indentation.

        Returns:
            str: JSON-formatted schema.
        """
        schema = self.extract_schema(df)
        json_schema_raw = schema.jsonValue()
        return json.dumps(json_schema_raw, indent=4 if pretty_json else None)

    def transform_df(
        self, df: DataFrame, keep_original_body: bool = False
    ) -> DataFrame:
        """
        Parse the JSON column into a StructType column.

        Args:
            df (DataFrame): Input DataFrame.
            keep_original_body (bool): If True and names match, error is raised.
                If False and names differ, drops original JSON column.

        Returns:
            DataFrame: DataFrame with parsed JSON column.

        Raises:
            ValueError: If attempting to overwrite the original JSON column.
        """
        if self._fields_have_same_name and keep_original_body:
            raise ValueError(
                f"The field {self.json_field} is overwritten by the extracted json. Give extracted field new name to keep original body."
            )

        df_string = df.withColumn(
            self.new_field_w_extracted_body, f.col(self.json_field).cast(t.StringType())
        )

        sample_jsons = df_string

        if self._data_limit:
            sample_jsons = sample_jsons.limit(self._data_limit)

        sample_jsons = sample_jsons.select(self.new_field_w_extracted_body).agg(
            f.first(self.new_field_w_extracted_body)
        )

        if self._data_limit:
            sample_jsons = sample_jsons.limit(self._data_limit)

        sample_jsons = sample_jsons.collect()[0][0]

        df_parsed = df_string.withColumn(
            self.new_field_w_extracted_body,
            f.from_json(
                f.col(self.new_field_w_extracted_body), f.schema_of_json(sample_jsons)
            ),
        )

        if (not keep_original_body) and (not self._fields_have_same_name):
            df_parsed = df_parsed.drop(self.json_field)

        return df_parsed
