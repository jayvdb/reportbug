#
# mailer module - Mail User Agent interface for reportbug
#   Written by Chris Lawrence <lawrencc@debian.org>
#   Copyright (C) 1999-2008 Chris Lawrence
#   Copyright (C) 2008-2019 Sandro Tosi <morph@debian.org>
#   Copyright (C) 2020 Nis Martensen <nis.martensen@web.de>
#
# This program is freely distributable per the following license:
#
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted,
#  provided that the above copyright notice appears in all copies and that
#  both that copyright notice and this permission notice appear in
#  supporting documentation.
#
#  I DISCLAIM ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING ALL
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL I
#  BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
#  DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
#  WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
#  ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
#  SOFTWARE.

import email
import email.policy
import re
import shlex
import shutil
import urllib


MAX_ARG_LENGTH = 130000  # the actual limit on linux is 131071


class Mua:
    def __init__(self, command):
        self._command = command
        self.executable = command.split()[0]

    def get_send_command(self, filename):
        cmd = self._command
        if '%s' not in cmd:
            cmd += ' %s'
        cmd = cmd % shlex.quote(filename)
        return cmd


class Gnus(Mua):
    def __init__(self):
        self.executable = 'emacsclient'

    def get_send_command(self, filename):
        elisp = """(progn
                      (load-file "/usr/share/reportbug/reportbug.el")
                      (tfheen-reportbug-insert-template "%s"))"""
        filename = re.sub("[\"\\\\]", "\\\\\\g<0>", filename)
        elisp = shlex.quote(elisp % filename)
        cmd = "emacsclient --no-wait --eval %s 2>/dev/null || emacs --eval %s" % (elisp, elisp)
        return cmd


class Mailto(Mua):
    def _uq(self, ins):
        return urllib.parse.quote(ins, safe='', errors='replace')

    def _get_headerparam(self, hdr, msg):
        parmstr = ""

        hd = msg[hdr]
        if hd:
            content = self._uq(''.join(hd.splitlines()))
            parmstr = "{}={}&".format(hdr, content)

        return parmstr

    def _msg_to_mailto(self, msg):
        mailto = "mailto:"
        mailto += self._uq(''.join(msg["to"].splitlines()))
        mailto += "?"

        for hdr in ["subject", "cc", "bcc"]:
            mailto += self._get_headerparam(hdr, msg)

        body = msg.get_payload(decode=True).decode(errors='replace')
        if body:
            try_mailto = mailto + 'body=' + self._uq(body)
            while len(try_mailto) > MAX_ARG_LENGTH:
                body = body[:-2000]
                if not body:
                    # should never happen
                    raise Exception('unreasonable message')
                body += '\n\n[ MAILBODY EXCEEDED REASONABLE LENGTH, OUTPUT TRUNCATED ]'
                try_mailto = mailto + 'body=' + self._uq(body)
            mailto = try_mailto

        return mailto.rstrip('?&')

    def get_send_command(self, filename):
        with open(filename, 'r') as fp:
            message = email.message_from_file(fp, policy=email.policy.compat32)

        cmd = '{} "{}"'.format(self.executable, self._msg_to_mailto(message))
        return cmd


MUA = {
    'mutt': Mua('mutt -H'),
    'neomutt': Mua('neomutt -H'),
    'mh': Mua('/usr/bin/mh/comp -use -file'),
    'nmh': Mua('/usr/bin/mh/comp -use -file'),
    'gnus': Gnus(),
    'claws-mail': Mua('claws-mail --compose-from-file'),
    'alpine': Mailto('alpine -url'),
    'pine': Mailto('pine -url'),
    'evolution': Mailto('evolution'),
    'kmail': Mailto('kmail'),
    'thunderbird': Mailto('thunderbird -compose'),
    'sylpheed': Mailto('sylpheed --compose'),
    'xdg-email': Mailto('xdg-email'),
}


def mua_is_supported(mua):
    # check if the mua is supported by reportbug
    if isinstance(mua, Mua) or mua in MUA.keys():
        return True
    return False


def mua_exists(mua):
    # check if the mua is available on the system
    if isinstance(mua, str):
        try:
            mua = MUA[mua]
        except KeyError:
            return False
    if shutil.which(mua.executable):
        return True
    return False
