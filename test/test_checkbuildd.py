import unittest

import pytest

from reportbug import checkbuildd


class TestCheckbuildd(unittest.TestCase):
    @pytest.mark.network  # marking the test as using network
    def test_check_built(self):
        built = checkbuildd.check_built('gkrellm', 60)
        self.assertTrue(built)

        # check for a non-existing package, that triggers a failure
        built = checkbuildd.check_built('non-existing-pkg', 60)
        self.assertFalse(built)
