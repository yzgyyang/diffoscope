# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015      Jérémy Bobbio <lunar@debian.org>
#             2016-2017 Mattia Rizzolo <mattia@debian.org>
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
import functools
import importlib.util
import subprocess

from distutils.spawn import find_executable
from distutils.version import LooseVersion


def file_version():
    return subprocess.check_output(
        ('file', '-v'),
    ).decode('utf-8').splitlines()[0].split('-')[-1]


def tools_missing(*required):
    return not required or any(find_executable(x) is None for x in required)


def skip_unless_tools_exist(*required):
    return pytest.mark.skipif(
        tools_missing(*required),
        reason="requires {}".format(" and ".join(required)),
    )


def skip_if_tool_version_is(tool, actual_ver, target_ver, vcls=LooseVersion):
    if tools_missing(tool):
        return pytest.mark.skipif(True, reason="requires {}".format(tool))
    if callable(actual_ver):
        actual_ver = actual_ver()
    return pytest.mark.skipif(
        vcls(str(actual_ver)) == vcls(str(target_ver)),
        reason="requires {} != {} ({} detected)".format(
            tool, target_ver, actual_ver)
    )


def skip_unless_tool_is_at_least(tool, actual_ver, min_ver, vcls=LooseVersion):
    if tools_missing(tool) and module_is_not_importable(tool):
        return pytest.mark.skipif(True, reason="requires {}".format(tool))
    if callable(actual_ver):
        actual_ver = actual_ver()
    return pytest.mark.skipif(
        vcls(str(actual_ver)) < vcls(str(min_ver)),
        reason="requires {} >= {} ({} detected)".format(
            tool, min_ver, actual_ver)
    )


def skip_unless_tool_is_at_most(tool, actual_ver, max_ver, vcls=LooseVersion):
    if tools_missing(tool) and module_is_not_importable(tool):
        return pytest.mark.skipif(True, reason="requires {}".format(tool))
    if callable(actual_ver):
        actual_ver = actual_ver()
    return pytest.mark.skipif(
        vcls(str(actual_ver)) > vcls(str(max_ver)),
        reason="requires {} <= {} ({} detected)".format(
            tool, max_ver, actual_ver)
    )


def skip_unless_tool_is_between(tool, actual_ver, min_ver, max_ver, vcls=LooseVersion):
    if tools_missing(tool):
        return pytest.mark.skipif(True, reason="requires {}".format(tool))
    if callable(actual_ver):
        actual_ver = actual_ver()
    return pytest.mark.skipif(
        (vcls(str(actual_ver)) < vcls(str(min_ver))) or
        (vcls(str(actual_ver)) > vcls(str(max_ver))),
        reason="requires {} >= {} >= {} ({} detected)".format(min_ver, tool,
                                                              max_ver, actual_ver)
    )


def skip_if_binutils_does_not_support_x86():
    if tools_missing('objdump'):
        return skip_unless_tools_exist('objdump')

    return pytest.mark.skipif(
        'elf64-x86-64' not in get_supported_elf_formats(),
        reason="requires a binutils capable of reading x86-64 binaries"
    )


@functools.lru_cache()
def get_supported_elf_formats():
    return set(subprocess.check_output(
        ('objdump', '--info'),
    ).decode('utf-8').splitlines())


def module_is_not_importable(x):
    try:
        if importlib.util.find_spec(x) is None:
            return True
        # an existent module is not necessarily importable, e.g. if its child
        # modules are not available, e.g. if we are running diffoscope using a
        # non-default version of python, and the module uses extension modules
        # that haven't been compiled for this version
        importlib.import_module(x)
    except ImportError:
        # Probing for submodules (eg. ``debian.deb822``) will attempt to
        # import ``debian`` so we must handle that failing.
        return True


def skip_unless_module_exists(name):
    return pytest.mark.skipif(
        module_is_not_importable(name),
        reason="requires {} module".format(name),
    )


def skip_unless_file_version_is_at_least(version):
    return skip_unless_tool_is_at_least('file', file_version, version)
