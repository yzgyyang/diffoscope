# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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

import html
import re

re_diff_line_numbers = re.compile(
    r"(^|\n)@@ -(\d+),(\d+) \+(\d+),(\d+) @@(?=\n|$)"
)


def diff_ignore_line_numbers(diff):
    return re_diff_line_numbers.sub(r"\1@@ -XX,XX +XX,XX @@", diff)


def _collapse_line(line, escape=html.escape):
    len_ = len(escape(line))
    return str(len_ - 1) + "\n" if line[-1] == "\n" else str(len_)


def _diff_collapse_line(line):
    return (
        line[0] + _collapse_line(line[1:])
        if line and line[0] in '+- '
        else line
    )


def _expand_line(line):
    return (
        (int(line[:-1]) * ".") + "\n"
        if line[-1] == "\n"
        else (int(line) * ".")
    )


def _diff_expand_line(line):
    return (
        line[0] + _expand_line(line[1:]) if line and line[0] in '+- ' else line
    )


def diff_collapse(diff):
    return diff.map_lines(_diff_collapse_line, _collapse_line)


def diff_expand(diff):
    return diff.map_lines(_diff_expand_line, _expand_line)
