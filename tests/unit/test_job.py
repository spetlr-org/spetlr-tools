import unittest

from spetlrtools.test_job.RunDetails import clean_cluster_output


class TestJobTests(unittest.TestCase):
    def test_cluster_output_cleaning(self):
        result = clean_cluster_output(test_output_data)
        self.assertEqual(test_output_results, result)


test_output_data = """
2023-10-09T10:29:55.684+0000: 1066.353: [GC (Allocation Failure) [PSYoungGen: 1753490K->199077K(1760256K)] 3063728K->1519562K(6033920K), 0.0846213 secs] [Times: user=0.29 sys=0.01, real=0.09 secs]
2023-10-09T10:30:01.993+0000: 1072.662: [GC (GCLocker Initiated GC) [PSYoungGen: 1760165K->196114K(1848832K)] 3080702K->1530471K(6122496K), 0.0886842 secs] [Times: user=0.30 sys=0.01, real=0.09 secs]
2023-10-09T10:30:07.574+0000: 1078.243: [GC (Allocation Failure) [PSYoungGen: 1756178K->199299K(1847808K)] 3091565K->1544512K(6121472K), 0.0840475 secs] [Times: user=0.30 sys=0.00, real=0.09 secs]
2023-10-09T10:30:14.133+0000: 1084.802: [GC (Allocation Failure) [PSYoungGen: 1759363K->197368K(1851392K)] 3104576K->1556764K(6125056K), 0.0859015 secs] [Times: user=0.31 sys=0.00, real=0.09 secs]
2023-10-09T10:30:19.316+0000: 1089.985: [GC (Allocation Failure) [PSYoungGen: 1761528K->199275K(1849344K)] 3120924K->1568725K(6123008K), 0.0876728 secs] [Times: user=0.29 sys=0.01, real=0.09 secs]
2023-10-09T10:30:25.098+0000: 1095.767: [GC (Allocation Failure) [PSYoungGen: 1763435K->194436K(1857536K)] 3132885K->1577608K(6131200K), 0.0850645 secs] [Times: user=0.31 sys=0.00, real=0.08 secs]
2023-10-09T10:30:30.978+0000: 1101.647: [GC (Allocation Failure) [PSYoungGen: 1768836K->194021K(1853440K)] 3152008K->1588673K(6127104K), 0.0880306 secs] [Times: user=0.29 sys=0.01, real=0.09 secs]
2023-10-09T10:30:47.248+0000: 1117.917: [GC (Allocation Failure) [PSYoungGen: 1768421K->192321K(1866752K)] 3163073K->1599473K(6140416K), 0.0831369 secs] [Times: user=0.29 sys=0.01, real=0.08 secs]
2023-10-09T10:30:53.782+0000: 1124.451: [GC (Allocation Failure) [PSYoungGen: 1784129K->193258K(1861632K)] 3191281K->1612206K(6135296K), 0.0839107 secs] [Times: user=0.29 sys=0.01, real=0.09 secs]
2023-10-09T10:30:58.717+0000: 1129.386: [GC (Allocation Failure) [PSYoungGen: 1785066K->192823K(1875968K)] 3204014K->1623625K(6149632K), 0.0944917 secs] [Times: user=0.29 sys=0.01, real=0.09 secs]
2023-10-09T10:31:05.549+0000: 1136.217: [GC (Allocation Failure) [PSYoungGen: 1803575K->191283K(1871360K)] 3234377K->1635844K(6145024K), 0.0888673 secs] [Times: user=0.30 sys=0.01, real=0.09 secs]
2023-10-09T10:31:10.772+0000: 1141.441: [GC (Allocation Failure) [PSYoungGen: 1802035K->193928K(1884160K)] 3246596K->1648234K(6157824K), 0.0832717 secs] [Times: user=0.29 sys=0.01, real=0.08 secs]
2023-10-09T10:31:17.376+0000: 1148.045: [GC (Allocation Failure) [PSYoungGen: 1822088K->191917K(1880576K)] 3276394K->1659750K(6154240K), 0.0925184 secs] [Times: user=0.29 sys=0.01, real=0.10 secs]
2023-10-09T10:31:23.334+0000: 1154.003: [GC (Allocation Failure) [PSYoungGen: 1820077K->193708K(1891840K)] 3287910K->1671490K(6165504K), 0.0854999 secs] [Times: user=0.30 sys=0.01, real=0.09 secs]
2023-10-09T10:31:29.494+0000: 1160.163: [GC (Allocation Failure) [PSYoungGen: 1837228K->196799K(1888256K)] 3315010K->1685956K(6161920K), 0.1013699 secs] [Times: user=0.33 sys=0.00, real=0.10 secs]
2023-10-09T10:31:36.686+0000: 1167.355: [GC (Allocation Failure) [PSYoungGen: 1840319K->195636K(1896448K)] 3329476K->1696851K(6170112K), 0.0859654 secs] [Times: user=0.30 sys=0.00, real=0.08 secs]
2023-10-09T10:31:42.998+0000: 1173.666: [GC (Allocation Failure) [PSYoungGen: 1849396K->199871K(1893888K)] 3350611K->1712473K(6167552K), 0.0926467 secs] [Times: user=0.31 sys=0.00, real=0.09 secs]
2023-10-09T10:31:50.508+0000: 1181.177: [GC (Allocation Failure) [PSYoungGen: 1853631K->197162K(1899520K)] 3366233K->1722006K(6173184K), 0.0927705 secs] [Times: user=0.29 sys=0.01, real=0.09 secs]
2023-10-09T10:31:55.688+0000: 1186.357: [GC (Allocation Failure) [PSYoungGen: 1857578K->198907K(1897472K)] 3382422K->1733634K(6171136K), 0.0937848 secs] [Times: user=0.30 sys=0.01, real=0.09 secs]
2023-10-09T10:32:01.173+0000: 1191.842: [GC (Allocation Failure) [PSYoungGen: 1859323K->204038K(1900032K)] 3394050K->1752297K(6173696K), 0.0930032 secs] [Times: user=0.30 sys=0.02, real=0.10 secs]
2023-10-09T10:32:05.717+0000: 1196.386: [GC (Allocation Failure) [PSYoungGen: 1868550K->200897K(1900544K)] 3416809K->1759363K(6174208K), 0.0888348 secs] [Times: user=0.32 sys=0.00, real=0.09 secs]
hello
"""
test_output_results = """
hello
"""
