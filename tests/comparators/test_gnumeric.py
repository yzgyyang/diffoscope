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

import pytest

from diffoscope.comparators.gnumeric import GnumericFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist
from ..utils.nonexisting import assert_non_existing

gnumeric1 = load_fixture('test1.gnumeric')
gnumeric2 = load_fixture('test2.gnumeric')


def test_identification(gnumeric1):
    assert isinstance(gnumeric1, GnumericFile)


def test_no_differences(gnumeric1):
    difference = gnumeric1.compare(gnumeric1)
    assert difference is None


@pytest.fixture
def differences(gnumeric1, gnumeric2):
    return gnumeric1.compare(gnumeric2).details


@skip_unless_tools_exist('ssconvert')
def test_diff(differences):
    expected_diff = get_data('gnumeric_expected_diff')
    assert differences[0].unified_diff == expected_diff


@skip_unless_tools_exist('ssconvert')
def test_compare_non_existing(monkeypatch, gnumeric1):
    assert_non_existing(monkeypatch, gnumeric1, has_null_source=False)
