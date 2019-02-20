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

from diffoscope.comparators.pgp import PgpFile, PgpSignature

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist
from ..utils.nonexisting import assert_non_existing

pgp1 = load_fixture('test1.pgp')
pgp2 = load_fixture('test2.pgp')
signature1 = load_fixture('test1.asc')
signature2 = load_fixture('test2.asc')


def test_identification(pgp1):
    assert isinstance(pgp1, PgpFile)


def test_no_differences(pgp1):
    difference = pgp1.compare(pgp1)
    assert difference is None


@pytest.fixture
def differences(pgp1, pgp2):
    return pgp1.compare(pgp2).details


@skip_unless_tools_exist('pgpdump')
def test_diff(differences):
    expected_diff = get_data('pgp_expected_diff')
    assert differences[0].unified_diff == expected_diff


@skip_unless_tools_exist('pgpdump')
def test_compare_non_existing(monkeypatch, pgp1):
    assert_non_existing(monkeypatch, pgp1, has_null_source=False)


def test_pgp_signature_identification(signature1, signature2):
    assert isinstance(signature1, PgpSignature)
    assert isinstance(signature2, PgpSignature)


@skip_unless_tools_exist('pgpdump')
def test_pgp_signature(signature1, signature2):
    difference = signature1.compare(signature2)
    assert difference.unified_diff == get_data('pgp_signature_expected_diff')
    assert difference.details[0].source1 == 'pgpdump'
    assert len(difference.details) == 1
