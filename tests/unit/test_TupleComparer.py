import unittest
from datetime import datetime, timedelta

from pyspark.sql import Row

from spetlrtools.testing.TupleComparer import TupleComparer


class TestTupleComparer(unittest.TestCase):
    def test_01_compare(self):
        tc1 = TupleComparer(Row(a=4, b=None, c=7))
        tc2 = TupleComparer(Row(a=4, b=None, c=None))
        self.assertLess(tc2, tc1)
        self.assertGreater(tc1, tc2)

    def test_02_sort(self):
        # Sort all rows even if they contain Nulls
        now = datetime.now()
        later = now + timedelta(hours=1)
        rows = [
            Row(a=now, b="None", c=None, d=None),
            Row(a=later, b=None, c=None, d=None),
            Row(a=now, b=None, c=None, d=None),
            Row(a=None, b=None, c=None, d=None),
            Row(a=None, b=None, c=0, d=None),
            Row(a=None, b=None, c=1, d=None),
            Row(a=None, b="None", c=1, d=None),
            Row(a=None, b=None, c=None, d=(3.5, True)),
            Row(a=None, b=None, c=None, d=(0.0, False)),
            Row(a=None, b=None, c=None, d=(None, True)),
        ]

        s = sorted(rows, key=TupleComparer)
        self.assertEqual(
            s,
            [
                Row(a=None, b=None, c=None, d=None),
                Row(a=None, b=None, c=None, d=(None, True)),
                Row(a=None, b=None, c=None, d=(0.0, False)),
                Row(a=None, b=None, c=None, d=(3.5, True)),
                Row(a=None, b=None, c=0, d=None),
                Row(a=None, b=None, c=1, d=None),
                Row(a=None, b="None", c=1, d=None),
                Row(a=now, b=None, c=None, d=None),
                Row(a=now, b="None", c=None, d=None),
                Row(a=later, b=None, c=None, d=None),
            ],
        )
