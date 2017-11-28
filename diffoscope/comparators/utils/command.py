# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
#
# diffoscope is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# diffoscope is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import io
import abc
import logging
import shlex
import subprocess
import threading

logger = logging.getLogger(__name__)


class Command(object, metaclass=abc.ABCMeta):
    def __init__(self, path):
        self._path = path

    def start(self):
        logger.debug("Executing %s", ' '.join([shlex.quote(x) for x in self.cmdline()]))
        self._stdin = self.stdin()
        # "stdin" used to be a feeder but we didn't need the functionality so
        # it was simplified into the current form. it can be recovered from git
        # the extra functionality is needed in the future. alternatively,
        # consider using a shell pipeline ("sh -ec $script") to implement what
        # you need, because that involves much less code - like it or not (I
        # don't) shell is still the most readable option for composing processes
        self._process = subprocess.Popen(self.cmdline(),
                                         shell=False, close_fds=True,
                                         env=self.env(),
                                         stdin=self._stdin,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        self._stderr = io.BytesIO()
        self._stderr_line_count = 0
        self._stderr_reader = threading.Thread(target=self._read_stderr)
        self._stderr_reader.daemon = True
        self._stderr_reader.start()

    @property
    def path(self):
        return self._path

    def stdin(self):
        return None

    @abc.abstractmethod
    def cmdline(self):
        raise NotImplementedError()

    def shell_cmdline(self):
        return ' '.join(map(lambda x: '{}' if x == self.path else shlex.quote(x), self.cmdline()))

    def env(self):
        return None  # inherit parent environment by default

    def filter(self, line):
        # Assume command output is utf-8 by default
        return line

    def poll(self):
        return self._process.poll()

    def terminate(self):
        return self._process.terminate()

    def wait(self):
        self._stderr_reader.join()
        returncode = self._process.wait()
        logger.debug(
            "%s returned (exit code: %d)",
            ' '.join([shlex.quote(x) for x in self.cmdline()]),
            returncode,
        )
        if self._stdin:
            self._stdin.close()
        return returncode

    MAX_STDERR_LINES = 50

    def _read_stderr(self):
        for line in iter(self._process.stderr.readline, b''):
            self._stderr_line_count += 1
            if self._stderr_line_count <= Command.MAX_STDERR_LINES:
                self._stderr.write(line)
        if self._stderr_line_count > Command.MAX_STDERR_LINES:
            self._stderr.write('[ {} lines ignored ]\n'.format(self._stderr_line_count - Command.MAX_STDERR_LINES).encode('utf-8'))
        self._process.stderr.close()

    @property
    def stderr_content(self):
        return self._stderr.getvalue().decode('utf-8', errors='replace')

    @property
    def stderr(self):
        return self._stderr

    @property
    def stdout(self):
        return self._process.stdout
