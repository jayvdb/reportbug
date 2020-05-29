import unittest
from unittest import mock

import pytest

from reportbug import utils
from reportbug import debbugs
from reportbug import urlutils

import re


class TestDebianbts(unittest.TestCase):
    def test_get_tags(self):
        # for each severity, for each mode
        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch'])

        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer'])

        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])

        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer'])


class TestInfofunc(unittest.TestCase):
    def test_dpkg_infofunc(self):
        info = debbugs.dpkg_infofunc()
        arch = utils.get_arch()
        self.assertIn('Architecture:', info)
        self.assertIn(arch, info)
        self.assertIn('Architecture: ' + arch, info)
        self.assertTrue(info.endswith('\n\n'))

        # save original method
        __save1 = utils.get_arch
        __save2 = utils.get_multiarch

        utils.get_arch = mock.MagicMock(return_value='non-existing-arch')
        info = debbugs.dpkg_infofunc()
        self.assertIn('non-existing-arch', info)
        self.assertTrue(info.endswith('\n\n'))

        # test with get_arch() returning None
        utils.get_arch = mock.MagicMock(return_value=None)
        info = debbugs.dpkg_infofunc()
        self.assertIn('Architecture: ?', info)
        self.assertTrue(info.endswith('\n\n'))

        # test with a dummy m-a setup
        utils.get_multiarch = mock.MagicMock(return_value='multi-arch-ified')
        info = debbugs.dpkg_infofunc()
        self.assertIn('Foreign Architectures:', info)
        self.assertIn('multi-arch-ified', info)
        self.assertIn('Foreign Architectures: multi-arch-ified', info)

        utils.get_arch = __save1
        utils.get_multiarch = __save2
        del __save1
        del __save2

    def test_debian_infofunc(self):
        info = debbugs.debian_infofunc()
        self.assertIn('Architecture:', info)

    def test_ubuntu_infofunc(self):
        info = debbugs.ubuntu_infofunc()
        self.assertIn('Architecture:', info)

    def test_generic_infofunc(self):
        info = debbugs.generic_infofunc()
        self.assertIn('Architecture:', info)


class TestMiscFunctions(unittest.TestCase):
    def test_yn_bool(self):
        self.assertEqual(debbugs.yn_bool(None), 'no')
        self.assertEqual(debbugs.yn_bool('no'), 'no')
        self.assertEqual(debbugs.yn_bool('yes'), 'yes')
        self.assertEqual(debbugs.yn_bool('dummy string'), 'yes')

    def test_convert_severity(self):

        # lists of bts systems, severity and the expected value in return
        sevs = [('debbugs', 'critical', 'critical'),
                ('debbugs', 'non-critical', 'normal'),
                (None, 'dummy', 'dummy'),
                ('gnats', 'important', 'serious'),
                ('gnats', 'dummy', 'dummy')]

        for type, severity, value in sevs:
            self.assertEqual(debbugs.convert_severity(severity, type), value)

    @pytest.mark.network  # marking the test as using network
    def test_pseudopackages_in_sync(self):

        dictparse = re.compile(r'([^\s]+)\s+(.+)', re.IGNORECASE)

        bdo_list = {}
        pseudo = urlutils.urlopen('https://bugs.debian.org/pseudopackages/pseudo-packages.description')
        for l in pseudo.splitlines():
            m = dictparse.search(l)
            bdo_list[m.group(1)] = m.group(2)

        # we removed base from reportbug
        del bdo_list['base']
        # remove debian-maintainers pseudo, it's been deprecated
        del bdo_list['debian-maintainers']
        # uniform reportbug customized descriptions
        for customized in ['ftp.debian.org', ]:
            bdo_list[customized] = debbugs.debother[customized]
        self.maxDiff = None
        self.assertEqual(debbugs.debother, bdo_list)


class TestGetReports(unittest.TestCase):

    @pytest.mark.network  # marking the test as using network
    def test_get_reports(self):
        data = debbugs.get_reports('reportbug', timeout=60)
        self.assertGreater(data[0], 0)

    @pytest.mark.network  # marking the test as using network
    def test_get_report(self):
        buginfo, bodies = debbugs.get_report(415801, 120)
        self.assertEqual(buginfo.bug_num, 415801)
        self.assertEqual(buginfo.subject,
                         'reportbug: add support for SOAP interface to BTS')

        # relative to bts#637994, report with messages without a header
        buginfo, bodies = debbugs.get_report(503300, 120)
        self.assertGreater(len(bodies), 0)

    @pytest.mark.network  # marking the test as using network
    def test_bts796759(self):
        # verify accessing WNPP happens correctly, now that BTS
        # access has to be done in batches
        data = debbugs.get_reports('wnpp', 120, source=True)
        self.assertGreater(data[0], 0)


class TestUrlFunctions(unittest.TestCase):
    def test_cgi_report_url(self):
        self.assertCountEqual(debbugs.cgi_report_url('debian', 123).split('?')[1].split('&'),
                              'bug=123&archived=False&mbox=no'.split('&'))
        self.assertIsNone(debbugs.cgi_report_url('default', 123))

    def test_cgi_package_url(self):
        self.assertCountEqual(debbugs.cgi_package_url('debian', 'reportbug').split('?')[1].split('&'),
                              'repeatmerged=yes&archived=no&pkg=reportbug'.split('&'))
        self.assertCountEqual(debbugs.cgi_package_url('debian', 'reportbug', source=True).split('?')[1].split('&'),
                              'src=reportbug&archived=no&repeatmerged=yes'.split('&'))
        self.assertCountEqual(debbugs.cgi_package_url('debian', 'reportbug', version='5.0').split('?')[1].split('&'),
                              'pkg=reportbug&version=5.0&repeatmerged=yes&archived=no'.split('&'))

    def test_get_package_url(self):
        self.assertCountEqual(debbugs.get_package_url('debian', 'reportbug').split('?')[1].split('&'),
                              'archived=no&pkg=reportbug&repeatmerged=yes'.split('&'))

    def test_get_report_url(self):
        self.assertCountEqual(debbugs.get_report_url('debian', 123).split('?')[1].split('&'),
                              'bug=123&archived=False&mbox=no'.split('&'))
