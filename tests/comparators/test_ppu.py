# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
#             2015 Paul Gevers <elbrus@debian.org>
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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from diffoscope.comparators import FilesystemFile
from diffoscope.comparators.ppu import PpuFile

from utils import skip_unless_tools_exist, data, load_fixture, \
    assert_non_existing

# These test files were taken from two different builds of the Debian package
# fp-units-castle-game-engine (version 5.1.1-2 on amd64) on the Debian
# reproducible build infrastructure. The files were originally called
# castletexturefont_dejavusans_10.ppu which are generated during package
# building of the cge package from dejavusans font in the fonts-dejavu package.

file1 = load_fixture(data('test1.ppu'))
file2 = load_fixture(data('test2.ppu'))

@skip_unless_tools_exist('ppudump')
def test_identification(file1):
    # If the recognition had failed due to mismatching ppu version it'll be a
    # FilesystemFile.
    if isinstance(file1, FilesystemFile):
        pytest.xfail(reason="mismatch between system ppu and fixture")

    assert isinstance(file1, PpuFile)

def test_no_differences(file1):
    difference = file1.compare(file1)
    assert difference is None

@pytest.fixture
def differences(file1, file2):
    return file1.compare(file2).details

@skip_unless_tools_exist('ppudump')
def test_diff(differences):
    print(differences[0].unified_diff)
    expected_diff = open(data('ppu_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('ppudump')
def test_compare_non_existing(monkeypatch, file1):
    assert_non_existing(monkeypatch, file1, has_null_source=False)
