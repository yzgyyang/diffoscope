# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2018 Joachim Breitner <nomeata@debian.org>
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

from diffoscope.comparators.wasm import WasmFile

from ..utils.data import load_fixture, get_data
from ..utils.tools import skip_unless_tools_exist
from ..utils.nonexisting import assert_non_existing


wasmmodule1 = load_fixture('hello1.wasm')
wasmmodule2 = load_fixture('hello2.wasm')


def test_identification(wasmmodule1):
    assert isinstance(wasmmodule1, WasmFile)


def test_no_differences(wasmmodule1):
    difference = wasmmodule1.compare(wasmmodule1)
    assert difference is None


@pytest.fixture
def differences(wasmmodule1, wasmmodule2):
    return wasmmodule1.compare(wasmmodule2).details


@skip_unless_tools_exist('wasm2wat')
def test_diff(differences):
    expected_diff = get_data('wasm_expected_diff')
    actual_diff = differences[0].unified_diff
    assert actual_diff == expected_diff


@skip_unless_tools_exist('wasm2wat')
def test_compare_non_existing(monkeypatch, wasmmodule1):
    assert_non_existing(monkeypatch, wasmmodule1, has_null_source=False)
