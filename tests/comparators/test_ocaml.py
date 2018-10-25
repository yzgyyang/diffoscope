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
import subprocess

from diffoscope.comparators.ocaml import OcamlInterfaceFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tool_is_at_least
from ..utils.nonexisting import assert_non_existing

cmi1 = load_fixture('test1.cmi')
cmi2 = load_fixture('test2.cmi')


def ocaml_version():
    try:
        out = subprocess.check_output(['ocaml', '-version'])
    except subprocess.CalledProcessError as e:
        out = e.output
    return out.decode('utf-8').split()[-1]


def test_identification(cmi1):
    assert isinstance(cmi1, OcamlInterfaceFile)


@pytest.fixture
def differences(cmi1, cmi2):
    return cmi1.compare(cmi2).details


def test_no_differences(cmi1):
    difference = cmi1.compare(cmi1)
    assert difference is None


@skip_unless_tool_is_at_least('ocamlobjinfo', ocaml_version, '4.05.0')
def test_diff(differences):
    expected_diff = get_data('ocaml_expected_diff')
    assert differences[0].unified_diff == expected_diff


@skip_unless_tool_is_at_least('ocamlobjinfo', ocaml_version, '4.05.0')
def test_compare_non_existing(monkeypatch, cmi1):
    assert_non_existing(monkeypatch, cmi1, has_null_source=False)
