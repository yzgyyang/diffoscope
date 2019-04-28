# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2010 Chris Lamb <lamby@debian.org>
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

from diffoscope.comparators.kbx import KbxFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist
from ..utils.nonexisting import assert_non_existing

kbx1 = load_fixture('test1.kbx')
kbx2 = load_fixture('test2.kbx')


def test_identification(kbx1):
    assert isinstance(kbx1, KbxFile)


def test_no_differences(kbx1):
    difference = kbx1.compare(kbx1)
    assert difference is None


@pytest.fixture
def differences(kbx1, kbx2):
    return kbx1.compare(kbx2).details


@skip_unless_tools_exist('kbxutil')
def test_diff(differences):
    with open('tests/data/kbx_expected_diff', 'w') as f:
        f.write(differences[0].unified_diff)
    expected_diff = get_data('kbx_expected_diff')
    assert differences[0].unified_diff == expected_diff


@skip_unless_tools_exist('kbxutil')
def test_compare_non_existing(monkeypatch, kbx1):
    assert_non_existing(monkeypatch, kbx1, has_null_source=False)
