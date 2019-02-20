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

import os
import diffoscope
import subprocess

from .utils.tools import skip_unless_tools_exist

BASE_DIR = os.path.dirname(os.path.abspath(diffoscope.__file__))


@skip_unless_tools_exist('black')
def test_code_is_black_clean():
    output = subprocess.check_output(
        ('black', '--diff', '.'), stderr=subprocess.PIPE
    ).decode('utf-8')

    # Display diff in "captured stdout call"
    print(output)

    assert len(output) == 0
