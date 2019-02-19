# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Chris Lamb <lamby@debian.org>
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

import os
import re
import logging
import subprocess

from diffoscope.tools import tool_required
from diffoscope.tempfiles import get_temporary_directory
from diffoscope.difference import Difference

from .utils.file import File
from .utils.archive import Archive
from .utils.command import Command

logger = logging.getLogger(__name__)


class AbootimgInfo(Command):
    @tool_required('abootimg')
    def cmdline(self):
        return ['abootimg', '-i', self.path]

    def filter(self, line):
        if line.startswith(b'* file name = '):
            return b''
        return line


class AndroidBootImgContainer(Archive):
    @property
    def path(self):
        return self._path

    @tool_required('abootimg')
    def open_archive(self):
        self._members = []
        self._unpacked = get_temporary_directory()

        logger.debug(
            "Extracting Android boot image to %s", self._unpacked.name
        )

        subprocess.check_call(
            ['abootimg', '-x', os.path.abspath(self.source.path)],
            cwd=self._unpacked.name,
            stdout=subprocess.PIPE,
        )

        self._members = sorted(os.listdir(self._unpacked.name))

        return self

    def close_archive(self):
        self._unpacked.cleanup()

    def extract(self, member_name, dest_dir):
        return os.path.join(self._unpacked.name, member_name)

    def get_member_names(self):
        return self._members


class AndroidBootImgFile(File):
    DESCRIPTION = "Android boot images"
    FILE_TYPE_RE = re.compile(r'^Android bootimg\b')
    CONTAINER_CLASS = AndroidBootImgContainer

    def compare_details(self, other, source=None):
        return [Difference.from_command(AbootimgInfo, self.path, other.path)]
