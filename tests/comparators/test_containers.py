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

from ..utils.data import load_fixture, get_data

gzip1 = load_fixture('containers/a.tar.gz')
gzip2 = load_fixture('containers/b.tar.gz')

xz1 = load_fixture('containers/a.tar.xz')
xz2 = load_fixture('containers/b.tar.xz')

bzip1 = load_fixture('containers/a.tar.bz2')
bzip2 = load_fixture('containers/b.tar.bz2')


@pytest.fixture
def differences_equal_gzip_xz(gzip1, xz1):
    return gzip1.compare(xz1).details


@pytest.fixture
def differences_equal_gzip_bzip2(gzip1, bzip1):
    return gzip1.compare(bzip1).details


@pytest.fixture
def differences_equal_bzip2_xz(bzip1, xz1):
    return bzip1.compare(xz1).details


@pytest.fixture
def differences_different_gzip_xz(gzip1, xz2):
    return gzip1.compare(xz2).details


@pytest.fixture
def differences_different_gzip_bzip2(gzip1, bzip2):
    return gzip1.compare(bzip2).details


@pytest.fixture
def differences_different_bzip2_xz(bzip1, xz2):
    return bzip1.compare(xz2).details


# Compares same content files, but with different extensions
def test_equal_content_gzip_xz_diff(differences_equal_gzip_xz):
    expected_diff = get_data('containers/equal_files_expected_bzip_xz_diff')
    assert differences_equal_gzip_xz[0].unified_diff == expected_diff


def test_equal_content_gzip_bzip2_diff(differences_equal_gzip_bzip2):
    expected_diff = get_data('containers/equal_files_expected_gzip_bzip2_diff')
    assert differences_equal_gzip_bzip2[0].unified_diff == expected_diff


@pytest.mark.skip(reason="Behavior not matching previous containers. Check needed.")
def test_equal_content_bzip2_xz_diff(differences_equal_bzip2_xz):
    assert differences_equal_bzip2_xz == []


# Compares different content files with different extensions
def test_different_content_gzip_xz_meta(differences_different_gzip_xz):
    expected_diff = get_data('containers/different_files_expected_gzip_xz_meta')
    assert differences_different_gzip_xz[0].unified_diff == expected_diff


def test_different_content_gzip_xz_diff(differences_different_gzip_xz):
    expected_diff = get_data('containers/different_files_expected_gzip_xz_diff')
    assert differences_different_gzip_xz[1].details[1].unified_diff == expected_diff


def test_different_content_gzip_bzip2_meta(differences_different_gzip_bzip2):
    expected_diff = get_data('containers/different_files_expected_gzip_bzip2_meta')
    assert differences_different_gzip_bzip2[0].unified_diff == expected_diff


def test_different_content_gzip_bzip2_diff(differences_different_gzip_bzip2):
    expected_diff = get_data('containers/different_files_expected_gzip_bzip2_diff')
    assert differences_different_gzip_bzip2[1].details[1].unified_diff == expected_diff


@pytest.mark.skip(reason="Behavior not matching previous containers. Check needed.")
def test_different_content_bzip2_xz_meta(differences_different_bzip2_xz):
    expected_diff = get_data('containers/different_files_expected_bzip2_xz_meta')
    assert differences_different_bzip2_xz[0].unified_diff == expected_diff


def test_different_content_bzip2_xz_diff(differences_different_bzip2_xz):
    expected_diff = get_data('containers/different_files_expected_bzip2_xz_diff')
    assert differences_different_bzip2_xz[0].details[1].unified_diff == expected_diff
