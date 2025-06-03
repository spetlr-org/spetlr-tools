import unittest

import spetlrtools.requirements


class RequirementsTest(unittest.TestCase):
    def test_function(self):
        freeze = spetlrtools.requirements.freeze_req(
            """
            pytest
            """,
            reject="pip",
        )
        deps = {lib["name"]: lib["version"] for lib in freeze}

        self.assertIn("pytest", deps)
        self.assertIn("iniconfig", deps)
        self.assertIn("pluggy", deps)
        self.assertNotIn("pip", deps)
