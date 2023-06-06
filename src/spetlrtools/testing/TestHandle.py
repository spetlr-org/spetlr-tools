from typing import Any, List, Union

from pyspark.sql import DataFrame
from spetlr.tables.TableHandle import TableHandle


class TestHandle(TableHandle):
    __test__ = False  # solves PytestCollectionWarning

    def __init__(self, provides: DataFrame = None):
        self.provides = provides
        self.overwritten = None
        self.appended = None
        self.truncated = False
        self.dropped = False
        self.dropped_and_deleted = False
        self.upserted = None
        self.upserted_join_cols = None
        self.comparison_col = None
        self.comparison_limit = None
        self.comparison_operator = None

    def read(self) -> DataFrame:
        if self.provides is not None:
            return self.provides
        else:
            raise AssertionError("TableHandle not readable.")

    def overwrite(self, df: DataFrame) -> None:
        self.overwritten = df

    def append(self, df: DataFrame) -> None:
        self.appended = df

    def truncate(self) -> None:
        self.truncated = True

    def drop(self) -> None:
        self.dropped = True

    def drop_and_delete(self) -> None:
        self.dropped_and_deleted = True

    def upsert(self, df: DataFrame, join_cols: List[str]) -> Union[DataFrame, None]:
        self.upserted = df
        self.upserted_join_cols = join_cols

    def delete_data(
        self, comparison_col: str, comparison_limit: Any, comparison_operator: str
    ) -> None:
        self.comparison_col = comparison_col
        self.comparison_limit = comparison_limit
        self.comparison_operator = comparison_operator
