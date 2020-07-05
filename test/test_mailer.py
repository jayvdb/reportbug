# coding=utf-8
import unittest
from unittest import mock

import pytest

from reportbug import mailer
import os.path
import email
import textwrap
import shutil


class TestMua(unittest.TestCase):
    def test_mua_is_supported(self):

        for mua in ('mh', 'nmh', 'gnus', 'mutt', 'claws-mail', 'xdg-email'):
            self.assertTrue(mailer.mua_is_supported(mua))

        self.assertFalse(mailer.mua_is_supported('mua-of-my-dreams'))

    def test_mua_exists(self):

        self.assertFalse(mailer.mua_exists('definitely-unsupported-mua'))
        self.assertFalse(mailer.mua_exists(mailer.Mua('definitely-unsupported-mua')))
        for mua in mailer.MUA:
            if shutil.which(mailer.MUA[mua].executable):
                self.assertTrue(mailer.mua_exists(mailer.MUA[mua]))
                self.assertTrue(mailer.mua_exists(mua))


message = textwrap.dedent(r"""
    Content-Type: text/plain; charset="utf-8"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 8bit
    From: Joe User <joeu@example.com>
    To: Debian Bug Tracking System <submit@bugs.debian.org>, Alice
      Maintainer <al@does-not-exist.org>
    Subject: buggy-pkg: doesn't work
      with continuation lines in subject
    Bcc: Debian Reportbug Maintainers <debian-reportbug@lists.debian.org>
    X-Reportbug-Version: 7.1.7

    Package: buggy-pkg
    Version: 2.4.1-1
    Severity: normal

    Dear Maintainer, reportbug/email needs to deal
    with stuff like non-ascii chars: »äÜø«,
     - words in 'single quotes',
     - words in "double" quotes,
     - words in `ls /` back quotes,
     - words in $(ls /usr/) brackets,
     - triple quotation ''' marks,
     - single escape \" quotation \' marks,
     ...
    """)[1:]


class TestMailtoMua(unittest.TestCase):
    def setUp(self):
        self.mailtomua = mailer.Mailto('xdg-email')
        self.message = email.message_from_string(message)
        self.mailto = self.mailtomua._msg_to_mailto(self.message)
        self.mdict = dict([x.split('=') for x in
            self.mailto.replace('mailto:','to=').replace('?','&').split('&')])

    def test_is_cmd(self):
        self.assertEqual(self.mailtomua.executable, "xdg-email")
        self.assertEqual(self.mailto[0:7], "mailto:")

    def test_body(self):
        self.assertTrue("body=Package%3A%20buggy-pkg" in self.mailto)
        self.assertTrue('%60ls%20/%60' in self.mdict['body'])
        self.assertTrue('%24%28ls%20/usr/%29' in self.mdict['body'])

    def test_to(self):
        self.assertTrue(
            "mailto:Debian%20Bug%20Tracking%20System%20%3Csubmit%40bugs.debian.org%3E"
            in self.mailto
        )
        self.assertTrue('Alice%20%20Maintainer' in self.mdict['to'])

    def test_bcc(self):
        self.assertTrue("bcc=Debian" in self.mailto)

    def test_subject(self):
        self.assertTrue("subject=buggy-pkg%3A%20doesn%27t%20work" in self.mailto)
        self.assertTrue('work%20%20with%20continuation%20line' in self.mdict['subject'])

class TestMailtoBig(unittest.TestCase):
    def setUp(self):
        self.mailtomua = mailer.Mailto('xdg-email')
        self.message = email.message_from_string(message+'.'*200000)
        self.attachments = ['/etc/hostname',
                '/etc/dpkg/origins/default',
                'certainly-not-existing-file',
                ]
        self.mailto = self.mailtomua._msg_to_mailto(self.message, self.attachments)
        self.arglist = [x.split('=') for x in
            self.mailto.replace('mailto:','to=').replace('?','&').split('&')]
        self.mdict = dict(self.arglist)

    def test_mailto_length(self):
        self.assertTrue(len(self.mailto) > 128000)
        self.assertTrue(len(self.mailto) < 130000)

    def test_attachments(self):
        # two of the specified attachments should make it to the mailto
        # string and be specified as separate arguments
        self.assertTrue([k for k, _ in self.arglist].count('attach') == 2)
        self.assertEqual([v for k, v in self.arglist if k == 'attach'],
                ['/etc/hostname', '/etc/dpkg/origins/default',])

    # rest is the same as for the small message test, just to be sure
    def test_is_cmd(self):
        self.assertEqual(self.mailtomua.executable, "xdg-email")
        self.assertEqual(self.mailto[0:7], "mailto:")

    def test_body(self):
        self.assertTrue("body=Package%3A%20buggy-pkg" in self.mailto)
        self.assertTrue('%60ls%20/%60' in self.mdict['body'])
        self.assertTrue('%24%28ls%20/usr/%29' in self.mdict['body'])

    def test_to(self):
        self.assertTrue(
            "mailto:Debian%20Bug%20Tracking%20System%20%3Csubmit%40bugs.debian.org%3E"
            in self.mailto
        )
        self.assertTrue('Alice%20%20Maintainer' in self.mdict['to'])

    def test_bcc(self):
        self.assertTrue("bcc=Debian" in self.mailto)

    def test_subject(self):
        self.assertTrue("subject=buggy-pkg%3A%20doesn%27t%20work" in self.mailto)
        self.assertTrue('work%20%20with%20continuation%20line' in self.mdict['subject'])
