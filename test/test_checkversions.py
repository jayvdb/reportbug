import unittest
from unittest import mock

import pytest

from reportbug import checkversions


class TestCheckversions(unittest.TestCase):
    def test_compare_versions(self):
        # <current, upstream>
        # 1 upstream newer than current
        # 0 same version or upstream none
        # -1 current newer than upstream
        self.assertEqual(checkversions.compare_versions('1.2.3', '1.2.4'), 1)

        self.assertEqual(checkversions.compare_versions('123', None), 0)
        self.assertEqual(checkversions.compare_versions('1.2.3', '1.2.3'), 0)
        self.assertEqual(checkversions.compare_versions(None, None), 0)
        self.assertEqual(checkversions.compare_versions('', '1.2.3'), 0)

        self.assertEqual(checkversions.compare_versions('1.2.4', '1.2.3'), -1)

    def test_later_version(self):
        # mock the test_compare_Versions() test

        self.assertEqual(checkversions.later_version('1.2.3', '1.2.4'), '1.2.4')

        self.assertEqual(checkversions.later_version('123', None), '123')
        self.assertEqual(checkversions.later_version('1.2.3', '1.2.3'), '1.2.3')
        self.assertIsNone(checkversions.later_version(None, None))
        self.assertEqual(checkversions.later_version('', '1.2.3'), '')

        self.assertEqual(checkversions.later_version('1.2.4', '1.2.3'), '1.2.4')


class TestNewQueue(unittest.TestCase):
    def test_bts704040(self):
        # return an iterable object, so that Deb822 (what parses the result)
        # will work
        pkg_in_new = """Source: procps
Binary: libprocps1-dev, procps, libprocps1
Version: 1:3.3.6-2 1:3.3.6-1 1:3.3.7-1 1:3.3.5-1
Architectures: source, amd64
Age: 4 months
Last-Modified: 1353190660
Queue: new
Maintainer: Craig Small <csmall@debian.org>
Changed-By: Craig Small <csmall@debian.org>
Distribution: experimental
Fingerprint: 5D2FB320B825D93904D205193938F96BDF50FEA5
Closes: #682082, #682083, #682086, #698482, #699716
Changes-File: procps_3.3.6-1_amd64.changes

Source: aaa
""".split('\n')

        # save the original checkversions.open_url() method
        save_open_url = checkversions.open_url

        checkversions.open_url = mock.MagicMock(return_value=pkg_in_new)

        res = checkversions.get_newqueue_available('procps', 60)

        self.assertEqual(list(res.keys())[0], 'experimental (new)')
        self.assertEqual(res['experimental (new)'], '1:3.3.7-1')

        # restore the original checkversions.open_url() method
        checkversions.open_url = save_open_url


class TestVersionAvailable(unittest.TestCase):
    @pytest.mark.network  # marking the test as using network
    def test_bts642032(self):
        vers = checkversions.get_versions_available('reportbug', 60)
        # check stable version is lower than unstable
        chk = checkversions.compare_versions(vers['stable'], vers['unstable'])
        self.assertGreaterEqual(chk, 0)

    @pytest.mark.network  # marking the test as using network
    def test_bts649649(self):
        # checking for non-existing package should not generate a traceback
        vers = checkversions.get_versions_available('blablabla', 60)
        self.assertEqual(vers, {})

    @pytest.mark.network  # marking the test as using network
    def test_bts673204(self):
        vers = checkversions.get_versions_available('texlive-xetex', 60)
        # squeeze (stable at this time) is the first suite where texlive-xetex
        # is arch:all
        self.assertIn('stable', vers)

    @pytest.mark.network  # marking the test as using network
    def test_codenames(self):
        vers = checkversions.get_versions_available('reportbug', 60, ['sid'])
        self.assertEqual(1, len(vers))
        self.assertEqual(list(vers.keys())[0], 'unstable')

    def test_nosourceversion(self):
        mixedpkg = """astroid    | 0.14-2.1      | oldstable       | amd64, arm64, armel, armhf, i386, mips, mips64el, mipsel, ppc64el, s390x
astroid    | 0.15-7        | stable          | amd64, arm64, armel, armhf, i386, mips64el, mipsel, ppc64el, s390x
astroid    | 0.16-1        | testing         | amd64, arm64, armel, armhf, i386, mips64el, mipsel, ppc64el, s390x
astroid    | 0.16-1        | unstable        | amd64, arm64, armel, armhf, i386, mips64el, mipsel, ppc64el, s390x
astroid    | 1.2.1-3       | oldoldoldstable | source
astroid    | 1.4.9-1       | oldoldstable    | source
astroid    | 2.1.0-2       | oldstable       | source
astroid    | 2.5.1-1       | stable          | source
astroid    | 2.5.1-1       | testing         | source
astroid    | 2.5.1-1       | unstable        | source
"""
        # save the original checkversions.open_url() method
        save_open_url = checkversions.open_url

        checkversions.open_url = mock.MagicMock(return_value=mixedpkg)

        res = checkversions.get_versions_available('astroid', 60)

        self.assertEqual(res, {'oldstable': '0.14-2.1',
            'stable': '0.15-7',
            'testing': '0.16-1',
            'unstable': '0.16-1'})

        # restore the original checkversions.open_url() method
        checkversions.open_url = save_open_url
