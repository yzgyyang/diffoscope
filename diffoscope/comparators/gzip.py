# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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

import re
import logging
import subprocess

from diffoscope.tools import tool_required


from .utils.file import File
from .utils.archive import Archive

logger = logging.getLogger(__name__)


class GzipContainer(Archive):
    def open_archive(self):
        return self

    def close_archive(self):
        pass

    def get_member_names(self):
        return [self.get_compressed_content_name('.gz')]

    @tool_required('gzip')
    def extract(self, member_name, dest_dir):
        dest_path = self.get_path_name(dest_dir)
        logger.debug('gzip extracting to %s', dest_path)
        with open(dest_path, 'wb') as fp:
            subprocess.check_call(
                ["gzip", "--decompress", "--stdout", self.source.path],
                shell=False, stdout=fp, stderr=None)
        return dest_path


class GzipFile(File):
    DESCRIPTION = "Gzipped files"
    CONTAINER_CLASS = GzipContainer
    FILE_TYPE_RE = re.compile(r'^gzip compressed data\b')

    # Work around file(1) Debian bug #876316
    FALLBACK_FILE_EXTENSION_SUFFIX = ".gz"
    FALLBACK_FILE_TYPE_HEADER_PREFIX = b"\x1f\x8b"
