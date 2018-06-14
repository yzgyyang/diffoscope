# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2018 Xavier Briand <xavierbriand@gmail.com>
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

import shutil
import pytest

from diffoscope.comparators.lz4 import Lz4File
from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.utils.specialize import specialize

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist
from ..utils.nonexisting import assert_non_existing

lz41 = load_fixture('test1.lz4')
lz42 = load_fixture('test2.lz4')


def test_identification(lz41):
    assert isinstance(lz41, Lz4File)


def test_no_differences(lz41):
    difference = lz41.compare(lz41)
    assert difference is None


@pytest.fixture
def differences(lz41, lz42):
    return lz41.compare(lz42).details


@skip_unless_tools_exist('lz4')
def test_content_source(differences):
    assert differences[0].source1 == 'test1'
    assert differences[0].source2 == 'test2'


@skip_unless_tools_exist('lz4')
def test_content_source_without_extension(tmpdir, lz41, lz42):
    path1 = str(tmpdir.join('test1'))
    path2 = str(tmpdir.join('test2'))
    shutil.copy(lz41.path, path1)
    shutil.copy(lz42.path, path2)
    lz41 = specialize(FilesystemFile(path1))
    lz42 = specialize(FilesystemFile(path2))
    difference = lz41.compare(lz42).details
    assert difference[0].source1 == 'test1-content'
    assert difference[0].source2 == 'test2-content'


@skip_unless_tools_exist('lz4')
def test_content_diff(differences):
    expected_diff = get_data('text_ascii_expected_diff')
    assert differences[0].unified_diff == expected_diff


@skip_unless_tools_exist('lz4')
def test_compare_non_existing(monkeypatch, lz41):
    assert_non_existing(monkeypatch, lz41)
