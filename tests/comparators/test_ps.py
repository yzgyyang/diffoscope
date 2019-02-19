# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Reiner Herrmann <reiner@reiner-h.de>
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

import pytest
import subprocess

from diffoscope.comparators.ps import PsFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist, skip_unless_tool_is_at_least
from ..utils.nonexisting import assert_non_existing


ps1 = load_fixture('test1.ps')
ps2 = load_fixture('test2.ps')


def ps2ascii_version():
    return subprocess.check_output(('ps2ascii', '--version')).decode('utf-8')


def test_identification(ps1):
    assert isinstance(ps1, PsFile)


@skip_unless_tool_is_at_least('ps2ascii', ps2ascii_version, '9.21')
def test_no_differences(ps1):
    difference = ps1.compare(ps1)
    assert difference is None


@pytest.fixture
def differences(ps1, ps2):
    return ps1.compare(ps2)


@skip_unless_tool_is_at_least('ps2ascii', ps2ascii_version, '9.21')
def test_internal_diff(differences):
    expected_diff = get_data('ps_internal_expected_diff')
    assert differences.unified_diff == expected_diff


@skip_unless_tool_is_at_least('ps2ascii', ps2ascii_version, '9.26')
def test_text_diff(differences):
    computed_diff = differences.details[0].unified_diff.replace('\r\n', '\n')
    expected_diff = get_data('ps_text_expected_diff')
    assert computed_diff == expected_diff


@skip_unless_tools_exist('ps2ascii')
@skip_unless_tool_is_at_least('ps2ascii', ps2ascii_version, '9.21')
def test_compare_non_existing(monkeypatch, ps1):
    assert_non_existing(monkeypatch, ps1, has_null_source=False)
