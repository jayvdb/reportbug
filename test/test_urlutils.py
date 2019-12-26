import unittest

import pytest

from reportbug import urlutils


class TestNetwork(unittest.TestCase):

    @pytest.mark.network  # marking the test as using network
    def test_open_url(self):

        page = urlutils.open_url('https://bugs.debian.org/reportbug')
        self.assertIsNotNone(page)
