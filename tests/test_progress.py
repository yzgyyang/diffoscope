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
import pytest

from diffoscope.main import main

TEST_TAR1_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test1.tar')
TEST_TAR2_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test2.tar')


def run(capsys, *args):
    with pytest.raises(SystemExit) as exc:
        main(args)

    out, err = capsys.readouterr()

    return exc.value.code, out, err

def test_progress(capsys):
    ret, _, err = run(capsys, TEST_TAR1_PATH, TEST_TAR2_PATH, '--progress')

    assert ret == 1
    assert "ETA" in err
