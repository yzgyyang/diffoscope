# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2018 Chris Lamb <lamby@debian.org>
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

import subprocess

from diffoscope.tools import tool_required
from diffoscope.tempfiles import get_named_temporary_file
from diffoscope.difference import Difference

from .utils.file import File

from .missing_file import MissingFile


class GnumericFile(File):
    DESCRIPTION = "Gnumeric spreadsheets"
    FILE_EXTENSION_SUFFIX = '.gnumeric'

    @tool_required('ssconvert')
    def compare_details(self, other, source=None):
        if isinstance(other, MissingFile):
            return [Difference(
                None,
                self.name,
                other.name,
                comment="Trying to compare two non-existing files."
            )]

        return [Difference.from_text(
            self.dump(self),
            self.dump(other),
            self.name,
            other.name,
            source='ssconvert'
        )]

    def dump(self, file):
        t = get_named_temporary_file()

        subprocess.check_call((
            'ssconvert',
            '--export-type=Gnumeric_stf:stf_assistant',
            file.path,
            t.name,
        ))

        with open(t.name) as f:
            return f.read().strip()
