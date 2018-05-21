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

import sys
import pytest

from diffoscope.config import Config
from diffoscope.comparators.android import AndroidBootImgFile
from diffoscope.comparators.missing_file import MissingFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist

bootimg1 = load_fixture('android1.img')
bootimg2 = load_fixture('android2.img')

# abootimg misfires on big endian architectures
# Part of the bug: https://bugs.debian.org/725729
bearch = sys.byteorder == 'big'


def test_identification(bootimg1):
    assert isinstance(bootimg1, AndroidBootImgFile)


def test_no_differences(bootimg1):
    difference = bootimg1.compare(bootimg1)
    assert difference is None


@pytest.fixture
def differences(bootimg1, bootimg2):
    return bootimg1.compare(bootimg2).details


@skip_unless_tools_exist('abootimg')
@pytest.mark.skipif(bearch, reason='abootimg is buggy on BE architectures')
def test_diff(differences):
    expected_diff = get_data('android_expected_diff')
    assert differences[0].unified_diff == expected_diff


@skip_unless_tools_exist('abootimg')
@pytest.mark.skipif(bearch, reason='abootimg is buggy on BE architectures')
def test_compare_non_existing(monkeypatch, bootimg1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = bootimg1.compare(MissingFile('/nonexisting', bootimg1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
