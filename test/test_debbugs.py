import unittest
from unittest import mock

import pytest

from reportbug import utils
from reportbug import debbugs
from reportbug import urlutils

import re


class MockUI:
    def __init__(self, *args):
        self.ret = list(args)

    def get_string(self, *args, **kwargs):
        return self.ret.pop(0)

    def log_message(self, *args, **kwargs):
        return

    def long_message(self, *args, **kwargs):
        return

    def menu(self, *args, **kwargs):
        return self.ret.pop(0)

    def select_options(self, *args, **kwargs):
        return self.ret.pop(0)

    def yes_no(self, *args, **kwargs):
        return self.ret.pop(0)


class TestSpecials(unittest.TestCase):
    def test_handle_debian_ftp(self):
        with self.assertRaises(SystemExit) as cm:
            debbugs.handle_debian_ftp('reportbug', '', MockUI(None), None, 60)
        self.assertIsNone(debbugs.handle_debian_ftp('reportbug', '', MockUI('other'), None, 60))
        self.assertEqual(
                debbugs.handle_debian_ftp('reportbug', '', MockUI('RoQA', 'reportbug', None, 'is broken', 'n'), None, 60),
                ('RM: reportbug -- RoQA; is broken', 'normal', [], [], '', False))
        self.assertEqual(
                debbugs.handle_debian_ftp('reportbug', '', MockUI('override', 'reportbug', 'utils', 'important', None), None, 60),
                ('override: reportbug:utils/important', 'normal', [],
                    ['User: ftp.debian.org@packages.debian.org', 'Usertags: override', 'X-Debbugs-Cc: debian-boot@lists.debian.org'],
                    '(Describe here the reason for this change)', False))

    def test_handle_debian_release(self):
        with self.assertRaises(SystemExit) as cm:
            debbugs.handle_debian_release('reportbug', '', MockUI(None), None, 60)

        self.assertIsNone(debbugs.handle_debian_release('reportbug', '', MockUI('other'), None, 60))

    def test_handle_debian_release_binnmu(self):
        ret = debbugs.handle_debian_release('reportbug', '',
                MockUI('binnmu', 'reportbug', 'y', 'n', None, 'no change'),
                None, 60)
        self.assertTrue(ret[0].startswith('nmu: reportbug_'))
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['User: release.debian.org@packages.debian.org', 'Usertags: binnmu'])
        self.assertTrue(ret[4].startswith('nmu reportbug_'))
        self.assertIn('unstable', ret[4])
        self.assertTrue(ret[4].endswith('"no change"\n'))
        self.assertFalse(ret[5])

    def test_handle_debian_release_britney(self):
        ret = debbugs.handle_debian_release('reportbug', '',
                MockUI('britney', 'mysubject'),
                None, 60)
        self.assertEqual(ret[0], 'mysubject')
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['User: release.debian.org@packages.debian.org', 'Usertags: britney'])
        self.assertEqual(ret[4], '')
        self.assertTrue(ret[5])

    def test_handle_debian_release_transition(self):
        ret = debbugs.handle_debian_release('reportbug', '',
                MockUI('transition', 'reportbug', 'oldname', 'newname'),
                None, 60)
        self.assertEqual(ret[0], 'transition: reportbug')
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['User: release.debian.org@packages.debian.org', 'Usertags: transition'])
        self.assertTrue(ret[4].startswith('(please explain'))
        self.assertIn('Ben file:', ret[4])
        self.assertTrue(ret[4].endswith('"oldname";\n\n'))
        self.assertFalse(ret[5])

    def test_handle_debian_release_unblock(self):
        ret = debbugs.handle_debian_release('reportbug', '',
                MockUI('unblock', 'reportbug', 'y'),
                None, 60)
        self.assertTrue(ret[0].startswith('unblock: reportbug/'))
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['User: release.debian.org@packages.debian.org', 'Usertags: unblock'])
        self.assertTrue(ret[4].startswith('Please unblock package reportbug\n\n'))
        self.assertFalse(ret[5])

    def test_handle_debian_release_rm(self):
        ret = debbugs.handle_debian_release('reportbug', '',
                MockUI('rm', 'reportbug', 'y', 'n', 'y'),
                None, 60)
        self.assertTrue(ret[0].startswith('RM: reportbug/'))
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['User: release.debian.org@packages.debian.org', 'Usertags: rm'])
        self.assertEqual(ret[4], '(explain the reason for the removal here)\n')
        self.assertFalse(ret[5])
        with self.assertRaises(SystemExit) as cm:
            debbugs.handle_debian_release('reportbug', '',
                    MockUI('rm', 'reportbug', 'y', 'n', 'n'),
                    None, 60)

    def test_handle_debian_release_pu(self):
        ret = debbugs.handle_debian_release('reportbug', '',
                MockUI('oldstable-pu', 'reportbug'),
                None, 60)
        self.assertTrue(ret[0].startswith('oldstable-pu: package reportbug/'))
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['User: release.debian.org@packages.debian.org', 'Usertags: pu', 'Tags: oldstable'])
        self.assertTrue(ret[4].startswith('(Please provide enough information'))
        self.assertFalse(ret[5])

    def test_handle_wnpp(self):
        with self.assertRaises(SystemExit) as cm:
            debbugs.handle_wnpp('reportbug', '', MockUI(None), None, 60)

        ret = debbugs.handle_wnpp('reportbug', '',
                MockUI('RFA', 'reportbug'),
                None, 60)
        self.assertTrue(ret[0].startswith('RFA: reportbug'))
        self.assertEqual(ret[1], 'normal')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], ['Control: affects -1 src:reportbug'])
        self.assertTrue(ret[4].startswith('I request an adopter'))
        self.assertFalse(ret[5])

        ret = debbugs.handle_wnpp('reportbug', '',
                MockUI('RFP', 'reportbug-bugfree', 'bug-free version of reportbug'),
                None, 60, online=False)
        self.assertEqual(ret[0], "RFP: reportbug-bugfree -- bug-free version of reportbug")
        self.assertEqual(ret[1], 'wishlist')
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], [])
        self.assertTrue(ret[4].startswith('* Package name'))
        self.assertTrue(ret[5])

    def test_handle_installation_report(self):
        ret = debbugs.handle_installation_report('reportbug', '',
                MockUI('roboot', 'image url', None),
                None, 60)
        self.assertEqual(ret[0], "")
        self.assertEqual(ret[1], "")
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], [])
        self.assertTrue(ret[4].startswith('(Please provide'))
        self.assertTrue(ret[5])

    def test_handle_upgrade_report(self):
        ret = debbugs.handle_upgrade_report('reportbug', '', MockUI(), None, 60)
        self.assertEqual(ret[0], "")
        self.assertEqual(ret[1], "")
        self.assertEqual(ret[2], [])
        self.assertEqual(ret[3], [])
        self.assertTrue(ret[4].startswith('(Please provide'))
        self.assertTrue(ret[5])


class TestDebianbts(unittest.TestCase):
    def test_get_tags(self):
        # for each severity, for each mode
        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_NOVICE).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'ftbfs'])

        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'security', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_STANDARD).keys()),
                              ['a11y', 'lfs', 'l10n', 'd-i', 'upstream', 'ipv6', 'patch', 'newcomer', 'ftbfs'])

        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_ADVANCED).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])

        self.assertCountEqual(list(debbugs.get_tags('critical', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('grave', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('serious', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('important', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('does-not-build', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('normal', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('non-critical', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('minor', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])
        self.assertCountEqual(list(debbugs.get_tags('wishlist', utils.MODE_EXPERT).keys()),
                              ['a11y', 'l10n', 'd-i', 'ipv6', 'patch', 'lfs', 'upstream', 'security', 'newcomer', 'ftbfs'])


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
                              'bug=123&archived=False&mbox=no&mboxmaint=no'.split('&'))
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
                              'bug=123&archived=False&mbox=no&mboxmaint=no'.split('&'))
