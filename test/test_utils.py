# coding=utf-8
import unittest
from unittest import mock

import pytest

from reportbug import utils
import os.path
import platform
import debianbts
import subprocess


class TestUtils(unittest.TestCase):
    def test_modes_and_modelist(self):
        """Check MODES items and MODELIST are in sync"""

        self.assertCountEqual(list(utils.MODES.keys()), utils.MODELIST)


class TestEmail(unittest.TestCase):
    def test_check_email_addr(self):
        real_addr = 'debian-reportbug@lists.debian.org'

        self.assertTrue(utils.check_email_addr(real_addr))
        self.assertFalse(utils.check_email_addr('dummy'))
        self.assertFalse(utils.check_email_addr('nouser@nodomain'))
        self.assertFalse(utils.check_email_addr('.nouser@nodomain'))
        self.assertFalse(utils.check_email_addr('nouser.@nodomain'))
        self.assertFalse(utils.check_email_addr('nouser@.nodomain'))
        self.assertFalse(utils.check_email_addr('nouser@nodomain.'))
        self.assertFalse(utils.check_email_addr('too@many@at@signs'))

    def test_get_email_addr(self):
        email = 'Reportbug Maintainers <debian-reportbug@lists.debian.org>'
        name, email_addr = utils.get_email_addr(email)

        self.assertEqual(name, 'Reportbug Maintainers')
        self.assertEqual(email_addr, 'debian-reportbug@lists.debian.org')

    def test_get_email(self):
        name = 'Reportbug Maintainers'
        mail = 'debian-reportbug@lists.debian.org'

        n, m = utils.get_email(mail, name)

        self.assertEqual(name, n)
        self.assertEqual(mail, m)

    def test_get_user_id(self):
        name = 'Reportbug Maintainers'
        mail = 'debian-reportbug@lists.debian.org'
        addr = utils.get_user_id(mail, name)
        self.assertEqual(addr, "%s <%s>" % (name, mail))

        name = 'test'
        mail = 'faked'
        addr = utils.get_user_id(mail, name)
        self.assertIn(mail + '@', addr)

        mail = 'Reportbug Maintainers <debian-reportbug@lists.debian.org>'
        addr = utils.get_user_id(mail)
        self.assertEqual(mail, addr)

        mail = 'debian-reportbug@lists.debian.org'
        addr = utils.get_user_id(mail)
        self.assertIn(mail, addr)

    def test_bts848692(self):
        name = "name-with.special`chars'  "
        mail = 'nomail@nodomain.ext'
        addr = utils.get_user_id(mail, name)
        self.assertEqual(addr, '"%s" <%s>' % (name, mail))

        name = "Ńámé MìddlèNàmé Ŝüŗnâmè"
        mail = 'nomail@nodomain.ext'
        addr = utils.get_user_id(mail, name)
        self.assertEqual(addr, '=?utf-8?b?xYPDoW3DqSBNw6xkZGzDqE7DoG3DqSDFnMO8xZduw6Jtw6g=?= <nomail@nodomain.ext>')

    def test_find_rewritten(self):
        unittest.skip("Is utils.find_rewritten actually useful to someone? deprecate it?")


class TestPackages(unittest.TestCase):
    def test_get_package_status(self):
        status = utils.get_package_status('non-existing-package')

        (pkgversion, pkgavail, depends, recommends, conffiles, maintainer,
         installed, origin, vendor, reportinfo, priority, desc, src_name,
         fulldesc, state, suggests, section) = status

        self.assertIsNone(pkgversion)
        self.assertIsNone(pkgavail)
        self.assertEqual(depends, ())
        self.assertEqual(recommends, ())
        self.assertEqual(conffiles, ())
        self.assertIsNone(maintainer)
        self.assertFalse(installed)
        self.assertIsNone(origin)
        self.assertEqual(vendor, '')
        self.assertIsNone(reportinfo)
        self.assertIsNone(priority)
        self.assertIsNone(desc)
        self.assertIsNone(src_name)
        self.assertEqual(fulldesc, '')
        self.assertEqual(state, '')
        self.assertEqual(suggests, ())
        self.assertIsNone(section)

        # Using an 'Essential: yes' package, what's better than 'dpkg'?
        status = utils.get_package_status('dpkg')

        (pkgversion, pkgavail, depends, recommends, conffiles, maintainer,
         installed, origin, vendor, reportinfo, priority, desc, src_name,
         fulldesc, state, suggests, section) = status

        self.assertIsNotNone(pkgversion)
        self.assertEqual(pkgavail, 'dpkg')
        # let's just check Depends is not null
        self.assertIsNotNone(depends)
        self.assertIsNotNone(maintainer)
        self.assertTrue(installed)
        self.assertEqual(origin, 'debian')
        self.assertEqual(priority, 'required')
        self.assertIsNotNone(desc)
        self.assertIsNotNone(fulldesc)
        self.assertEqual(state, 'installed')
        self.assertEqual(section, 'admin')

        # it exploits the 'statuscache', it's already called before
        # so it's now in the cache
        status = utils.get_package_status('dpkg')

        status = utils.get_package_status('reportbug', avail=True)

        (pkgversion, pkgavail, depends, recommends, conffiles, maintainer,
         installed, origin, vendor, reportinfo, priority, desc, src_name,
         fulldesc, state, suggests, section) = status

        self.assertIsNotNone(pkgversion)
        self.assertEqual(pkgavail, 'reportbug')
        # let's just check Depends is not null
        self.assertIsNotNone(depends)
        self.assertIsNotNone(maintainer)
        self.assertEqual(priority, 'standard')
        self.assertIsNotNone(desc)
        self.assertIsNotNone(fulldesc)

        status = utils.get_package_status('python-matplotlib')

        (pkgversion, pkgavail, depends, recommends, conffiles, maintainer,
         installed, origin, vendor, reportinfo, priority, desc, src_name,
         fulldesc, state, suggests, section) = status

        self.assertIsNotNone(recommends)

    def test_bts791577(self):
        # Verify obsolete config files are correctly parsed

        # bonus points for testing also conffiles with spaces in the filename
        pkgstatus = """Conffiles:
 /etc/reportbug.conf 17b8e0850fa74d18b96ce5856321de0d
 /etc/reportbug with spaces.conf feedcafefeedcafefeedcafefeedcafe
 /etc/reportbug.conf.obsolete deadbeefdeadbeefdeadbeefdeadbeef obsolete
 /etc/reportbug with spaces and obsolete.conf cafebabecafebabecafebabecafebabe obsolete
        """

        pkg = 'test_bts791577'

        expected_conffiles = ['/etc/reportbug.conf',
                              '/etc/reportbug with spaces.conf',
                              '/etc/reportbug.conf.obsolete',
                              '/etc/reportbug with spaces and obsolete.conf']

        __save = utils.get_command_output
        utils.get_command_output = mock.MagicMock(return_value=pkgstatus)
        result = utils.get_package_status(pkg)
        conffile = [x[0] for x in result[4]]
        utils.get_command_output = __save
        del __save
        self.assertListEqual(conffile, expected_conffiles)

    def test_get_changed_config_files(self):
        status = utils.get_package_status('dpkg')

        (pkgversion, pkgavail, depends, recommends, conffiles, maintainer,
         installed, origin, vendor, reportinfo, priority, desc, src_name,
         fulldesc, state, suggests, section) = status

        confinfo, changed = utils.get_changed_config_files(conffiles)
        self.assertIsNotNone(confinfo)

    def test_find_package_for(self):
        result = utils.find_package_for('dpkg')
        self.assertNotEqual(result[1], {})

        filename = 'reportbug-bugfree'
        result = utils.find_package_for(filename, pathonly=True)
        self.assertEqual(result[0], filename)
        self.assertIsNone(result[1])

        result = utils.find_package_for('/usr/bin/reportbug')
        self.assertNotEqual(result[1], {})

        result = utils.find_package_for('/var/lib/dpkg/info/reportbug.md5sums')
        self.assertNotEqual(result[1], {})

        result = utils.find_package_for('/usr/bin/')
        self.assertNotEqual(result[1], {})

    def test_get_package_info(self):
        result = utils.get_package_info([])
        self.assertEqual(result, [])

        pkg = 'reportbug'
        result = utils.get_package_info([((pkg,), pkg)])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], pkg)

        # open package surely not available on my client systems
        # to cover line 568
        pkg = 'slapd'
        result = utils.get_package_info([((pkg,), pkg)])

        self.assertEqual(result[0][0], pkg)
        self.assertEqual(result[0][2], '<none>')

        result = utils.get_package_info([((pkg,), pkg)], skip_notfound=True)

        self.assertEqual(result, [])

        # package with a Provides
        # pkg = 'emacs'
        # result = utils.get_package_info([((pkg,), pkg)])

        # self.assertEqual(result[0][0], pkg)

    def test_bts683116(self):
        """Check Description and Description-LANG are recognized"""

        pkginfo = """Package: reportbug
Status: install ok installed
Version: 6.6.3
%s: reports bugs in the Debian distribution
                """
        pkg = 'reportbug'

        __save = subprocess.getoutput
        subprocess.getoutput = mock.MagicMock(return_value=pkginfo % 'Description')
        result = utils.get_package_status(pkg)
        self.assertEqual('reports bugs in the Debian distribution', result[11])
        subprocess.getoutput = mock.MagicMock(return_value=pkginfo % 'Description-en')
        result = utils.get_package_status(pkg)
        self.assertEqual('reports bugs in the Debian distribution', result[11])
        subprocess.getoutput = __save
        del __save

        __save = utils.get_dpkg_database
        utils.get_dpkg_database = mock.MagicMock(return_value=[pkginfo % 'Description', ])
        result = utils.get_package_info([((pkg,), pkg)])
        self.assertEqual('reports bugs in the Debian distribution', result[0][3])
        utils.get_dpkg_database = mock.MagicMock(return_value=[pkginfo % 'Description-en', ])
        result = utils.get_package_info([((pkg,), pkg)])
        self.assertEqual('reports bugs in the Debian distribution', result[0][3])
        utils.get_dpkg_database = __save
        del __save

    def test_packages_providing(self):
        pkg = 'editor'
        result = utils.packages_providing(pkg)

        self.assertGreater(len(result), 0)

    def test_get_avail_database(self):
        avail_db = utils.get_avail_database()
        entry = next(avail_db)
        self.assertIsNotNone(entry)


class TestSourcePackages(unittest.TestCase):
    def test_get_source_name(self):
        binpkg = 'python3-reportbug'
        src = utils.get_source_name(binpkg)
        self.assertEqual(src, 'reportbug')

        src = utils.get_source_name('reportbug-bugfree')
        self.assertIsNone(src)

    def test_get_source_package(self):
        src = 'reportbug'
        binpkgs = utils.get_source_package(src)
        self.assertCountEqual([bin[0] for bin in binpkgs], ['python3-reportbug', 'reportbug', 'reportbug-gtk'])

        bin = 'python3-reportbug'
        binpkgs_frombin = utils.get_source_package(bin)
        self.assertEqual(binpkgs, binpkgs_frombin)


class TestSystemInformation(unittest.TestCase):
    def test_lsb_release_info(self):
        res = utils.lsb_release_info()
        self.assertIn('Debian', res)

    def test_get_running_kernel_pkg(self):
        package = utils.get_running_kernel_pkg()

        self.assertIn(platform.release(), package)

    def test_get_multiarch(self):
        orig = utils.get_command_output

        utils.get_command_output = mock.MagicMock(return_value='')
        multiarch = utils.get_multiarch()
        self.assertEqual(multiarch, '')

        utils.get_command_output = mock.MagicMock(return_value='i386')
        multiarch = utils.get_multiarch()
        self.assertEqual(multiarch, 'i386')

        utils.get_command_output = mock.MagicMock(return_value='i386\namd64')
        multiarch = utils.get_multiarch()
        self.assertCountEqual(multiarch.split(', '), ['i386', 'amd64'])

        utils.get_command_output = orig

    def test_get_init_system(self):
        __save = os.path.isdir
        os.path.isdir = mock.MagicMock(return_value=True)
        init = utils.get_init_system()
        self.assertTrue(init.startswith('systemd'))
        os.path.isdir = __save
        del __save

        __save = subprocess.call
        subprocess.call = mock.MagicMock(return_value=0)
        init = utils.get_init_system()
        self.assertTrue(init.startswith('upstart'))
        subprocess.call = __save
        del __save

        __save1 = os.path.isfile
        __save2 = os.path.islink
        os.path.isfile = mock.MagicMock(return_value=True)
        os.path.islink = mock.MagicMock(return_value=False)
        init = utils.get_init_system()
        print(init)
        self.assertTrue(init.startswith('sysvinit'))
        os.path.isfile = __save1
        os.path.islink = __save2
        del __save1
        del __save2


class TestMua(unittest.TestCase):
    def test_mua_is_supported(self):

        for mua in ('mh', 'nmh', 'gnus', 'mutt', 'claws-mail'):
            self.assertTrue(utils.mua_is_supported(mua))

        self.assertFalse(utils.mua_is_supported('mua-of-my-dreams'))

    def test_mua_exists(self):

        for mua in ('mh', 'nmh', 'gnus', 'mutt', 'claws-mail'):
            if not utils.mua_exists(mua):
                self.fail("%s MUA program not available" % mua)

    def test_mua_name(self):

        for mua in ('mh', 'nmh', 'gnus', 'mutt', 'claws-mail'):
            self.assertIsInstance(utils.mua_name(mua), utils.Mua)

        self.assertEqual(utils.mua_name('mua-of-my-dreams'), 'mua-of-my-dreams')


class TestBugreportBody(unittest.TestCase):
    def test_get_dependency_info(self):

        pkg = 'reportbug'
        result = utils.get_dependency_info('reportbug', '')

        self.assertIn('no packages', result)

        result = utils.get_dependency_info('reportbug', [['dpkg']])
        self.assertIn('dpkg', result)

        # check for the provides stuff
        result = utils.get_dependency_info('reportbug', [['awk']])
        self.assertIn('awk', result)

    def test_bts657753(self):
        # check that non-existing deps gets a correct installation info
        # and not just the last one applied to anyone
        result = utils.get_dependency_info('reportbug',
                                           (('reportbug',), ('nonexisting',)))
        for line in result.split('\n'):
            if 'nonexisting' in line:
                self.assertFalse(line.startswith('ii'))

    def test_bts650659(self):
        # verify that the dependency list doesn't have tailing white spaces

        status = utils.get_package_status('reportbug')
        (pkgversion, pkgavail, depends, recommends, conffiles, maintainer,
         installed, origin, vendor, reportinfo, priority, desc, src_name,
         fulldesc, state, suggests, section) = status

        for l in [depends, recommends, suggests]:
            result = utils.get_dependency_info('reportbug', l)
            for line in result.split('\n'):
                self.assertEqual(line.rstrip(), line)

    def test_cleanup_msg(self):

        message = """Subject: unblock: reportbug/4.12.6
Package: release.debian.org
User: release.debian.org@packages.debian.org
Usertags: unblock
Severity: normal
Morph: cool
Control: testcontrol1
Control: testcontrol2
Continuation:
 header

Please unblock package reportbug

(explain the reason for the unblock here)

unblock reportbug/4.12.6

-- System Information:
Debian Release: squeeze/sid
  APT prefers unstable
  APT policy: (500, 'unstable'), (1, 'experimental')
Architecture: amd64 (x86_64)

Kernel: Linux 2.6.31-1-amd64 (SMP w/4 CPU cores)
Locale: LANG=en_US.UTF-8, LC_CTYPE=en_US.UTF-8 (charmap=UTF-8)
Shell: /bin/sh linked to /bin/bash"""
        header = ['X-Debbugs-CC: reportbug@packages.qa.debian.org']
        pseudos = ['Morph: cool', 'Control: testcontrol1', 'Control: testcontrol2']
        rtype = 'debbugs'
        body, headers, pseudo = utils.cleanup_msg(message, header, pseudos,
                                                  rtype)

        # check body content
        self.assertIn('reportbug/4.12.6', body)
        self.assertIn('System Information', body)

        # check expected headers are there
        h = dict(headers)
        self.assertIn('Subject', h)
        self.assertIn('X-Debbugs-CC', h)

        # check expected pseudo headers are there
        p = dict([p.split(': ') for p in pseudo])
        self.assertIn('Package', p)
        self.assertIn('Severity', p)
        self.assertIn('User', p)
        self.assertIn('Usertags', p)
        self.assertIn('Morph', p)

        # bts687679, verify 2 'Control' pseudo-headers are present
        for ph in pseudos:
            self.assertIn(ph, pseudo)

    @pytest.mark.network  # marking the test as using network
    def test_generate_blank_report(self):

        report = utils.generate_blank_report('reportbug', '1.2.3', 'normal',
                                             '', '', '', type='debbugs')
        self.assertIsNotNone(report)
        self.assertIn('Package: reportbug', report)
        self.assertIn('Version: 1.2.3', report)
        self.assertIn('Severity: normal', report)

        report = utils.generate_blank_report('reportbug', '1.2.3', 'normal',
                                             '', '', '', type='debbugs',
                                             issource=True)
        self.assertIn('Source: reportbug', report)

        # test with exinfo (represents the bug number if this is a followup):
        # int, string, unconvertible (to int) datatype
        report = utils.generate_blank_report('reportbug', '1.2.3', 'normal',
                                             '', '', '', type='debbugs',
                                             exinfo=123456)
        self.assertIn('Followup-For: Bug #123456', report)

        bug = debianbts.get_status([123456])[0]
        report = utils.generate_blank_report('reportbug', '1.2.3', 'normal',
                                             '', '', '', type='debbugs',
                                             exinfo=bug)
        self.assertIn('Followup-For: Bug #123456', report)

        with self.assertRaises(TypeError):
            report = utils.generate_blank_report('reportbug', '1.2.3', 'normal',
                                                 '', '', '', type='debbugs',
                                                 exinfo={'123456': ''})


class TestConfig(unittest.TestCase):
    # Use an "internal" file for testing
    def setUp(self):
        self._FILES = utils.FILES
        utils.FILES = [os.path.dirname(__file__) + '/data/reportbug.conf']

    def tearDown(self):
        utils.FILES = self._FILES

    def test_parse_config_files(self):
        desired_conf = {
            'bts': 'debian',
            'check_available': True,
            'check_uid': False,
            'debconf': False,
            'dontquery': False,
            'editor': 'emacs -nw',
            'email': 'debian-reportbug@lists.debian.org',
            'envelopefrom': 'debian-reportbug@lists.debian.org',
            'headers': ['X-Reportbug-Testsuite: this is the test suite'],
            'http_proxy': 'http://proxy.example.com:3128/',
            'interface': 'gtk',
            'keyid': 'deadbeef',
            'max_attachment_size': 1024000,
            'mbox_reader_cmd': 'mutt -f %s',
            'mirrors': ['this_is_a_bts_mirror'],
            'mode': 'novice',
            'mta': '/usr/sbin/sendmail',
            'nocc': False,
            'nocompress': False,
            'noconf': False,
            'offline': True,
            'paranoid': True,
            'query_src': False,
            'realname': 'Reportbug Maintainers',
            'replyto': 'We dont care <dev@null.org>',
            'sendto': 'submit',
            'severity': 'normal',
            'sign': 'gpg',
            'smtphost': 'reportbug.debian.org:587',
            'smtppasswd': 'James Bond',
            'smtptls': True,
            'smtpuser': 'Bond',
            'template': True,
            'verify': True}

        args = utils.parse_config_files()
        for conf in desired_conf:
            self.assertIn(conf, args)
            self.assertEqual(desired_conf[conf], args[conf])

        # mua returns an instance of utils.Mua, need to check differently
        self.assertIn('mua', args)
        self.assertIsInstance(args['mua'], utils.Mua)

    def test_bts579891(self):
        lex = utils.our_lex('realname "Paul \\"TBBle\\" Hampson"', posix=True)
        option = lex.get_token()
        self.assertEqual(option, 'realname')
        realname = lex.get_token()
        self.assertEqual(realname, 'Paul "TBBle" Hampson')


class TestControl(unittest.TestCase):
    def test_parse_bug_control_file(self):
        ctrl_file = os.path.dirname(__file__) + '/data/control'

        submitas, submitto, reportwith, supplemental = \
            utils.parse_bug_control_file(ctrl_file)

        self.assertEqual(submitas, 'reportbug2')
        self.assertEqual(submitto, 'debian-reportbug@lists.debian.org')
        self.assertIn('python', reportwith)
        self.assertIn('perl', reportwith)
        self.assertIn('python', supplemental)
        self.assertIn('perl', supplemental)


class TestPaths(unittest.TestCase):
    def test_search_path_for(self):
        p = 'not-existing'
        res = utils.search_path_for(p)
        self.assertIsNone(res)

        p = '/tmp'
        res = utils.search_path_for(p)
        self.assertEqual(p, res)

        p = 'dpkg'
        res = utils.search_path_for(p)
        self.assertEqual(res, '/usr/bin/dpkg')


class TestEditor(unittest.TestCase):
    def test_which_editor(self):
        res = utils.which_editor()
        self.assertIsNotNone(res)

        e = 'reportbug-editor'
        res = utils.which_editor(e)
        self.assertEqual(e, res)


class TestSearch(unittest.TestCase):
    def test_search_pipe(self):
        f = 'reportbug'

        dlocate = True
        pipe, dloc = utils.search_pipe(f, dlocate)
        res = pipe.readlines()
        pipe.close()

        self.assertEqual(dloc, dlocate)
        self.assertGreater(len(res), 0)

        dlocate = False
        pipe, dloc = utils.search_pipe(f, dlocate)
        res = pipe.readlines()
        pipe.close()

        self.assertEqual(dloc, dlocate)
        self.assertGreater(len(res), 0)


class TestDpkg(unittest.TestCase):
    def test_query_dpkg_for(self):
        p = 'reportbug'
        dlocate = True
        res = utils.query_dpkg_for(p, dlocate)

        self.assertEqual(res[0], p)
        self.assertGreater(len(list(res[1].keys())), 0)

        dlocate = False
        res = utils.query_dpkg_for(p, dlocate)

        self.assertEqual(res[0], p)
        self.assertGreater(len(list(res[1].keys())), 0)

        # to trigger 'Try again without dlocate if no packages found'
        p = 'blablabla'
        dlocate = True
        res = utils.query_dpkg_for(p, dlocate)

        self.assertEqual(res[0], p)
        self.assertEqual(res[1], {})


class TestMisc(unittest.TestCase):
    def test_first_run(self):
        isfirstrun = utils.first_run()
        self.assertIsNotNone(isfirstrun)

    def test_exec_and_parse_bugscript(self):
        handler = os.path.dirname(__file__) + '/../share/handle_bugscript'
        bugscript_file = os.path.dirname(__file__) + '/data/bugscript'

        (rc, h, ph, t, a) = utils.exec_and_parse_bugscript(handler, bugscript_file)

        self.assertIn('python', t)
        self.assertIn('debian', t)
        self.assertIn('From: morph@dummy.int', h)
        self.assertIn('User: morph@debian.org', ph)
        self.assertIn('/etc/fstab', a)

    def test_check_package_name(self):
        self.assertTrue(utils.check_package_name('reportbug'))
        self.assertTrue(utils.check_package_name('ab'))
        self.assertFalse(utils.check_package_name('a'))
        self.assertFalse(utils.check_package_name('.a'))
        self.assertFalse(utils.check_package_name('dfffff       '))
        self.assertFalse(utils.check_package_name('reportbug_reportbug'))
        self.assertTrue(utils.check_package_name('reportbug+love-war.com'))
        self.assertTrue(utils.check_package_name('reportbug2001'))
        self.assertFalse(utils.check_package_name('UPPERCASE'))
        self.assertFalse(utils.check_package_name('((()))'))
