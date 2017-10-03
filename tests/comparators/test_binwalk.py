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

import pytest

from diffoscope.comparators.binwalk import BinwalkFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist, skip_unless_module_exists
from ..utils.nonexisting import assert_non_existing

binwalk1 = load_fixture('test1.binwalk')
binwalk2 = load_fixture('test2.binwalk')


@skip_unless_module_exists('binwalk')
def test_identification(binwalk1, binwalk2):
    assert isinstance(binwalk1, BinwalkFile)
    assert isinstance(binwalk2, BinwalkFile)


@skip_unless_module_exists('binwalk')
def test_no_differences(binwalk1):
    difference = binwalk1.compare(binwalk1)
    assert difference is None


@pytest.fixture
def comparison(binwalk1, binwalk2):
    return binwalk1.compare(binwalk2)


@skip_unless_tools_exist('cpio')
@skip_unless_module_exists('binwalk')
def test_listing(comparison):
    differences = comparison.details
    assert comparison.comments == ["comprises of 2 embedded members"]
    assert differences[0].source1 == '.cpio file embedded at offset 0'
    assert differences[1].source2 == '.cpio file embedded at offset 600'

    expected_diff = get_data('binwalk_expected_diff')
    assert differences[0].details[0].unified_diff == expected_diff


@skip_unless_tools_exist('cpio')
@skip_unless_module_exists('binwalk')
def test_symlink(comparison):
    differences = comparison.details
    assert differences[0].details[1].source1 == 'dir/link'
    assert differences[0].details[1].comment == 'symlink'
    expected_diff = get_data('symlink_expected_diff')
    assert differences[0].details[1].unified_diff == expected_diff


@skip_unless_tools_exist('cpio')
@skip_unless_module_exists('binwalk')
def test_compare_non_existing(monkeypatch, binwalk1):
    assert_non_existing(monkeypatch, binwalk1)
