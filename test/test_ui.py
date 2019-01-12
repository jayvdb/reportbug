""" Unit test for reportbug.ui module """

import unittest

from reportbug import ui
from reportbug.ui import __LOADED_UIS as LOADED_UIS


class TestUI(unittest.TestCase):

    def test_ui(self):
        self.assertCountEqual(ui.AVAILABLE_UIS, ['text', 'urwid', 'gtk'])

    def test_getUI(self):
        for loaded_ui in list(LOADED_UIS.keys()):
            self.assertEqual(ui.getUI(loaded_ui), LOADED_UIS[loaded_ui])

        self.assertEqual(ui.getUI('non-existing'), LOADED_UIS['text'])
