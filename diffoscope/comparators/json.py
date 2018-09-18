# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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

import json
import collections

from diffoscope.difference import Difference

from .utils.file import File

try:
    import jsondiff
except ImportError:  # noqa
    jsondiff = None


class JSONFile(File):
    DESCRIPTION = "JSON files"

    @classmethod
    def recognizes(cls, file):
        with open(file.path, 'rb') as f:
            # Try fuzzy matching for JSON files
            if not file.name.endswith('.json'):
                buf = f.read(10)
                if not any(x in buf for x in b'{['):
                    return False
                f.seek(0)

            try:
                file.parsed = json.loads(
                    f.read().decode('utf-8', errors='ignore'),
                    object_pairs_hook=collections.OrderedDict,
                )
            except ValueError:
                return False

        return True

    def compare_details(self, other, source=None):
        difference = Difference.from_text(
            self.dumps(self),
            self.dumps(other),
            self.path,
            other.path,
        )

        if difference:
            self.compare_with_jsondiff(difference, other)

            return [difference]

        difference = Difference.from_text(
            self.dumps(self, sort_keys=False),
            self.dumps(other, sort_keys=False),
            self.path,
            other.path,
            comment="ordering differences only",
        )

        return [difference]

    def compare_with_jsondiff(self, difference, other):
        if jsondiff is None:
            return

        a = getattr(self, 'parsed', {})
        b = getattr(other, 'parsed', {})

        try:
            diff = {repr(x): y for x, y in jsondiff.diff(a, b).items()}
        except Exception:
            return

        difference.add_comment("Similarity: {}%".format(
            jsondiff.similarity(a, b),
        ))

        difference.add_comment("Differences: {}".format(
            json.dumps(diff, indent=2, sort_keys=True),
        ))

    @staticmethod
    def dumps(file, sort_keys=True):
        if not hasattr(file, 'parsed'):
            return ""
        return json.dumps(file.parsed, indent=4, sort_keys=sort_keys)
