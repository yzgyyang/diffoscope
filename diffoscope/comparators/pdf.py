# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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

import re

from diffoscope.tools import tool_required
from diffoscope.difference import Difference

from .utils.file import File
from .utils.command import Command

try:
    import PyPDF2
except ImportError:  # noqa
    PyPDF2 = None


class Pdftotext(Command):
    @tool_required('pdftotext')
    def cmdline(self):
        return ['pdftotext', self.path, '-']


class PdfFile(File):
    DESCRIPTION = "PDF documents"
    FILE_TYPE_RE = re.compile(r'^PDF document\b')

    def compare_details(self, other, source=None):
        xs = []

        if PyPDF2 is not None:
            difference = Difference.from_text(
                self.dump_pypdf2_metadata(self),
                self.dump_pypdf2_metadata(other),
                self.path,
                other.path,
            )
            if difference:
                difference.add_comment("Document info")
            xs.append(difference)

        xs.append(Difference.from_command(Pdftotext, self.path, other.path))

        return xs

    @staticmethod
    def dump_pypdf2_metadata(file):
        try:
            pdf = PyPDF2.PdfFileReader(file.path)
            document_info = pdf.getDocumentInfo()
        except PyPDF2.utils.PdfReadError as exc:
            return "(Could not extract metadata: {})".format(exc)

        xs = []
        for k, v in sorted(document_info.items()):
            xs.append("{}: {!r}".format(k.lstrip('/'), v))

        return "\n".join(xs)
