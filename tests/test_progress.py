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
import sys
import json
import pytest

from distutils.version import LooseVersion

from diffoscope.main import main
from diffoscope.progress import ProgressManager, StatusFD

from .utils.tools import skip_unless_module_exists

TEST_TAR1_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test1.tar')
TEST_TAR2_PATH = os.path.join(os.path.dirname(__file__), 'data', 'test2.tar')


def run(capsys, *args):
    with pytest.raises(SystemExit) as exc:
        main(args)

    out, err = capsys.readouterr()

    return exc.value.code, out, err


def progressbar_version():
    import progressbar

    return progressbar.__version__


@pytest.fixture
def progressbar_err():
    # This fixture returns an expected error message depending on progressbar
    # version, from the lowest to the highest.
    expected_err = {'3.19': 'ETA', '3.34': ''}

    actual_ver = progressbar_version()

    for k, v in expected_err.items():
        if LooseVersion(actual_ver) < LooseVersion(k):
            return v

    return ''


@skip_unless_module_exists('progressbar')
def test_progress(capsys, progressbar_err):
    ret, _, err = run(capsys, TEST_TAR1_PATH, TEST_TAR2_PATH, '--progress')

    assert ret == 1
    assert progressbar_err in err


def test_status_fd(capsys):
    ProgressManager().register(StatusFD(sys.stderr))

    ret, _, err = run(capsys, TEST_TAR1_PATH, TEST_TAR2_PATH)

    assert ret == 1

    # Parse lines and ensure we emitted at least one line
    output = [json.loads(x) for x in err.splitlines()]
    assert output

    # Ensure each line is valid
    for x in output:
        assert 'msg' in x
        assert x['current'] <= x['total']

    # Last line should mark us as "complete"
    assert output[-1]['current'] == output[-1]['total']
