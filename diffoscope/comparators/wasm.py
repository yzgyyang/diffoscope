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

from diffoscope.tools import tool_required
from diffoscope.difference import Difference

from .utils.file import File
from .utils.command import Command

WASM_MAGIC = b"\x00asm"


class Wasm2Wat(Command):
    @tool_required('wasm2wat')
    def cmdline(self):
        return ['wasm2wat', '--no-check', self.path]


class WasmFile(File):
    DESCRIPTION = "WebAssembly binary module"
    FILE_EXTENSION_SUFFIX = '.wasm'

    @classmethod
    def recognizes(cls, file):
        if not super().recognizes(file):
            return False

        return file.file_header.startswith(WASM_MAGIC)

    def compare_details(self, other, source=None):
        return [Difference.from_command(Wasm2Wat, self.path, other.path)]
