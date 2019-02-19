# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Juliana Oliveira R <juliana.orod@gmail.org>
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

import itertools

from ..utils.data import load_fixture, get_data
from ..utils.tools import (
    skip_unless_tools_exist,
    skip_unless_file_version_is_at_least,
)

gzip1 = load_fixture('containers/a.tar.gz')
gzip2 = load_fixture('containers/b.tar.gz')

xz1 = load_fixture('containers/a.tar.xz')
xz2 = load_fixture('containers/b.tar.xz')

bzip1 = load_fixture('containers/a.tar.bz2')
bzip2 = load_fixture('containers/b.tar.bz2')

TYPES = "gzip bzip2 xz".split()


@pytest.fixture
def set1(gzip1, bzip1, xz1):
    return dict(zip(TYPES, [gzip1, bzip1, xz1]))


@pytest.fixture
def set2(gzip2, bzip2, xz2):
    return dict(zip(TYPES, [gzip2, bzip2, xz2]))


def expected_magic_diff(ext1, ext2):
    meta1 = get_data('containers/magic_%s' % ext1)
    meta2 = get_data('containers/magic_%s' % ext2)
    return "@@ -1 +1 @@\n" + "-" + meta1 + "+" + meta2


def expected_type_diff(ext1, ext2):
    return "@@ -1 +1 @@\n-%sFile\n+%sFile\n" % (
        ext1.capitalize(),
        ext2.capitalize(),
    )


# Compares same content files, but with different extensions


@skip_unless_tools_exist('xz')
@skip_unless_file_version_is_at_least('5.33')
def test_equal(set1):
    for x, y in itertools.product(TYPES, TYPES):
        diff = set1[x].compare(set1[y])
        if x == y:
            assert diff is None
        else:
            differences = diff.details
            assert differences[0].unified_diff == expected_magic_diff(
                x, y
            ), "{} {}".format(x, y)
            assert differences[1].unified_diff == expected_type_diff(x, y)


# Compares different content files with different extensions


@skip_unless_tools_exist('xz')
@skip_unless_file_version_is_at_least('5.33')
def test_different(set1, set2):
    for x, y in itertools.product(TYPES, TYPES):
        expected_diff = get_data('containers/different_files_expected_diff')
        differences = set1[x].compare(set2[y]).details
        if x == y:
            assert differences[0].details[1].unified_diff == expected_diff
        else:
            assert differences[0].unified_diff == expected_magic_diff(
                x, y
            ), "{} {}".format(x, y)
            assert differences[1].unified_diff == expected_type_diff(x, y)
            assert differences[2].details[1].unified_diff == expected_diff
