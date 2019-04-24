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
import io
import os
import errno
import fcntl
import hashlib
import logging
import threading
import subprocess

from multiprocessing.dummy import Queue

from diffoscope.tempfiles import get_temporary_directory

from .tools import get_tool_name, tool_required
from .config import Config

DIFF_CHUNK = 4096

logger = logging.getLogger(__name__)
re_diff_change = re.compile(r'^([+-@]).*', re.MULTILINE)


class DiffParser(object):
    RANGE_RE = re.compile(
        # example: '@@ -26814,9 +26814,8 @@'
        rb'''
          ^
            @@\s+
              -
              (?P<start1>\d+)(,(?P<len1>\d+))?
            \s+
              \+
              (?P<start2>\d+)(,(?P<len2>\d+))?
            \s+@@
          $
        ''',
        re.VERBOSE,
    )

    def __init__(self, output, end_nl_q1, end_nl_q2):
        self._output = output
        self._end_nl_q1 = end_nl_q1
        self._end_nl_q2 = end_nl_q2
        self._action = self.read_headers
        self._diff = io.BytesIO()
        self._success = False
        self._remaining_hunk_lines = None
        self._block_len = None
        self._direction = None
        self._end_nl = None
        self._max_lines = Config().max_diff_block_lines_saved

    @property
    def diff(self):
        return self._diff.getvalue().decode('UTF-8', errors='replace')

    @property
    def success(self):
        return self._success

    def parse(self):
        for line in self._output.split(b'\n'):
            self._action = self._action(line)

        self._action = None
        self._success = True

    def read_headers(self, line):
        if not line:
            return None

        if line.startswith(b'---'):
            return self.read_headers

        if line.startswith(b'+++'):
            return self.read_headers

        found = DiffParser.RANGE_RE.match(line)

        if not found:
            raise ValueError('Unable to parse diff headers: %r' % line)

        self._diff.write(line + b'\n')
        if found.group('len1'):
            self._remaining_hunk_lines = int(found.group('len1'))
        else:
            self._remaining_hunk_lines = 1
        if found.group('len2'):
            self._remaining_hunk_lines += int(found.group('len2'))
        else:
            self._remaining_hunk_lines += 1

        self._direction = None

        return self.read_hunk

    def read_hunk(self, line):
        if not line:
            return None

        if line[:1] == b' ':
            self._remaining_hunk_lines -= 2
        elif line[:1] == b'+':
            self._remaining_hunk_lines -= 1
        elif line[:1] == b'-':
            self._remaining_hunk_lines -= 1
        elif line[:1] == b'\\':
            # When both files don't end with \n, do not show it as a difference
            if self._end_nl is None:
                end_nl1 = self._end_nl_q1.get()
                end_nl2 = self._end_nl_q2.get()
                self._end_nl = end_nl1 and end_nl2
            if not self._end_nl:
                return self.read_hunk
        elif self._remaining_hunk_lines == 0:
            return self.read_headers(line)
        else:
            raise ValueError('Unable to parse diff hunk: %r' % line)

        self._diff.write(line + b'\n')

        if line[:1] in (b'-', b'+'):
            if line[:1] == self._direction:
                self._block_len += 1
            else:
                self._block_len = 1
                self._direction = line[:1]

            if self._block_len >= self._max_lines:
                return self.skip_block
        else:
            self._block_len = 1
            self._direction = line[:1]

        return self.read_hunk

    def skip_block(self, line):
        if self._remaining_hunk_lines == 0 or line[:1] != self._direction:
            removed = self._block_len - Config().max_diff_block_lines_saved
            if removed:
                self._diff.write(
                    b'%s[ %d lines removed ]\n' % (self._direction, removed)
                )
            return self.read_hunk(line)

        self._block_len += 1
        self._remaining_hunk_lines -= 1

        return self.skip_block


@tool_required('diff')
def run_diff(fifo1, fifo2, end_nl_q1, end_nl_q2):
    cmd = [get_tool_name('diff'), '-aU7', fifo1, fifo2]

    logger.debug("Running %s", ' '.join(cmd))

    p = subprocess.run(
        cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    parser = DiffParser(p.stdout, end_nl_q1, end_nl_q2)
    parser.parse()

    logger.debug(
        "%s: returncode %d, parsed %s",
        ' '.join(cmd),
        p.returncode,
        parser.success,
    )

    if not parser.success and p.returncode not in (0, 1):
        raise subprocess.CalledProcessError(p.returncode, cmd, output=diff)

    if p.returncode == 0:
        return None

    return parser.diff


class FIFOFeeder(threading.Thread):
    def __init__(self, feeder, fifo_path, end_nl_q=None, daemon=True, *args):
        os.mkfifo(fifo_path)
        super().__init__(daemon=daemon)
        self.feeder = feeder
        self.fifo_path = fifo_path
        self.end_nl_q = Queue() if end_nl_q is None else end_nl_q
        self._exception = None
        self._want_join = threading.Event()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.join()

    def run(self):
        try:
            # Try to open the FIFO nonblocking, so we can periodically check
            # if the main thread wants us to wind down.  If it does, there's no
            # more need for the FIFO, so stop the thread.
            while True:
                try:
                    fd = os.open(self.fifo_path, os.O_WRONLY | os.O_NONBLOCK)
                except OSError as e:
                    if e.errno != errno.ENXIO:
                        raise
                    elif self._want_join.is_set():
                        return
                else:
                    break

            # Now clear the fd's nonblocking flag to let writes block normally.
            fcntl.fcntl(fd, fcntl.F_SETFL, 0)

            with open(fd, 'wb') as fifo:
                # The queue works around a unified diff limitation: if there's
                # no newlines in both don't make it a difference
                end_nl = self.feeder(fifo)
                self.end_nl_q.put(end_nl)
        except Exception as error:
            self._exception = error

    def join(self):
        self._want_join.set()
        super().join()
        if self._exception is not None:
            raise self._exception


class _Feeder:
    """
    A 'feeder' is a specialized writer.

    A 'feeder' is a callable that takes as argument a writeable file, and
    writes to it.  Feeders can transform the written data, truncate it,
    checksum it, and so on.  The callable must return True to represent that
    the data had a terminating newline, and False otherwise.

    Feeders are created by the functions make_feeder_from_raw_reader() and
    empty_file_feeder().  The returned objects are closures, and are not
    (currently?) instances of any particular class.
    """

    pass


def empty_file_feeder():
    """
    Returns a feeder that simulates an empty file.

    See _Feeder for feeders.
    """

    def feeder(f):
        return False

    return feeder


def make_feeder_from_raw_reader(in_file, filter=None):
    """
    Create a feeder that checksums, truncates, and transcodes the data.  The
    optional argument FILTER is a callable that gets passed each line, and
    returns the line that should be used in its stead.  (There is no facility
    for FILTER to discard a line entirely.)

    See _Feeder for feeders.
    """

    def feeder(out_file):
        h = None
        end_nl = False
        max_lines = Config().max_diff_input_lines
        line_count = 0

        if max_lines < float("inf"):
            h = hashlib.sha1()

        for buf in in_file:
            line_count += 1
            out = filter(buf) if filter else buf
            if h:
                h.update(out)
            if line_count < max_lines:
                out_file.write(out)
            end_nl = buf[-1] == '\n'

        if h and line_count >= max_lines:
            out_file.write(
                "[ Too much input for diff (SHA1: {}) ]\n".format(
                    h.hexdigest()
                ).encode('utf-8')
            )
            end_nl = True

        return end_nl

    return feeder


def diff(feeder1, feeder2):
    tmpdir = get_temporary_directory().name

    fifo1_path = os.path.join(tmpdir, 'fifo1')
    fifo2_path = os.path.join(tmpdir, 'fifo2')
    with FIFOFeeder(feeder1, fifo1_path) as fifo1, FIFOFeeder(
        feeder2, fifo2_path
    ) as fifo2:
        return run_diff(fifo1_path, fifo2_path, fifo1.end_nl_q, fifo2.end_nl_q)


def diff_split_lines(diff, keepends=True):
    lines = diff.split("\n")
    if not keepends:
        return lines
    return [line + "\n" for line in lines[:-1]] + (
        [lines[-1]] if lines[-1] else []
    )


def reverse_unified_diff(diff):
    assert isinstance(diff, str)
    res = []
    # XXX - should move to just use plain bytes nearly everywhere until ready
    # to print instead of using strings internally as well.
    for line in diff_split_lines(diff):
        line = line.encode('utf-8', errors='replace')
        assert isinstance(line, bytes)
        found = DiffParser.RANGE_RE.match(line)

        if found:
            before = found.group('start2')
            if found.group('len2') is not None:
                before += b',' + found.group('len2')

            after = found.group('start1')
            if found.group('len1') is not None:
                after += b',' + found.group('len1')

            res.append(b'@@ -%s +%s @@\n' % (before, after))
        elif line.startswith(b'-'):
            res.append(b'+')
            res.append(line[1:])
        elif line.startswith(b'+'):
            res.append(b'-')
            res.append(line[1:])
        else:
            res.append(line)
    return b''.join(res).decode('utf-8', errors='replace')


def color_unified_diff(diff):
    RESET = '\033[0m'
    RED, GREEN, CYAN = '\033[31m', '\033[32m', '\033[0;36m'

    def repl(m):
        return '{}{}{}'.format(
            {'-': RED, '@': CYAN, '+': GREEN}[m.group(1)], m.group(0), RESET
        )

    return re_diff_change.sub(repl, diff)


DIFFON = "\x01"
DIFFOFF = "\x02"
MAX_WF_SIZE = 1024  # any higher, and linediff takes >1 second and >200MB RAM


def _linediff_sane(x):
    # turn non-printable chars into "."
    return "." if ord(x) < 32 and x not in '\t\n' else x


def diffinput_truncate(s, sz):
    # Truncate, preserving uniqueness
    if len(s) > sz:
        s = s[
            :sz
        ] + "[ ... truncated by diffoscope; len: {}, SHA1: {} ... ]".format(
            len(s[sz:]), hashlib.sha1(s[sz:].encode('utf-8')).hexdigest()
        )
    return s


def linediff(s, t, diffon, diffoff):
    # calculate common prefix/suffix, easy optimisation to WF
    prefix = os.path.commonprefix((s, t))
    if prefix:
        s = s[len(prefix) :]
        t = t[len(prefix) :]
    suffix = os.path.commonprefix((s[::-1], t[::-1]))[::-1]
    if suffix:
        s = s[: -len(suffix)]
        t = t[: -len(suffix)]

    # truncate so WF doesn't blow up RAM
    s = diffinput_truncate(s, MAX_WF_SIZE)
    t = diffinput_truncate(t, MAX_WF_SIZE)
    l1, l2 = zip(*linediff_simplify(linediff_wagnerfischer(s, t)))

    def to_string(k, v):
        sanev = "".join(_linediff_sane(c) for c in v)
        return (diffon + sanev + diffoff) if k else sanev

    s1 = ''.join(to_string(*p) for p in l1)
    t1 = ''.join(to_string(*p) for p in l2)
    return prefix + s1 + suffix, prefix + t1 + suffix


def linediff_wagnerfischer(s, t):
    '''
    Line diff algorithm, originally from diff2html.

    https://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm

    Finds the minimum (levenshtein) edit distance between two strings, but has
    quadratic performance O(m*n).
    '''
    m, n = len(s), len(t)
    d = [[(0, 0) for i in range(n + 1)] for i in range(m + 1)]

    d[0][0] = (0, (0, 0))
    for i in range(1, m + 1):
        d[i][0] = (i, (i - 1, 0))
    for j in range(1, n + 1):
        d[0][j] = (j, (0, j - 1))

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                cost = 0
            else:
                cost = 1
            d[i][j] = min(
                (d[i - 1][j][0] + 1, (i - 1, j)),
                (d[i][j - 1][0] + 1, (i, j - 1)),
                (d[i - 1][j - 1][0] + cost, (i - 1, j - 1)),
            )

    coords = []
    coord = (m, n)
    while coord != (0, 0):
        coords.insert(0, coord)
        x, y = coord
        coord = d[x][y][1]

    for coord in coords:
        cx, cy = coord
        child_val = d[cx][cy][0]

        father_coord = d[cx][cy][1]
        fx, fy = father_coord
        father_val = d[fx][fy][0]

        diff = (cx - fx, cy - fy)

        if diff == (0, 1):
            yield (False, ""), (True, t[fy])
        elif diff == (1, 0):
            yield (True, s[fx]), (False, "")
        elif child_val - father_val == 1:
            yield (True, s[fx]), (True, t[fy])
        else:
            assert s[fx] == t[fy]
            yield (False, s[fx]), (False, t[fy])


def linediff_simplify(g):
    """Simplify the output of WF."""
    current = None
    for l, r in g:
        if not current:
            current = l, r
        elif current[0][0] == l[0] and current[1][0] == r[0]:
            current = (
                (l[0], current[0][1] + l[1]),
                (r[0], current[1][1] + r[1]),
            )
        else:
            yield current
            current = l, r
    if current:
        yield current


class SideBySideDiff(object):
    """Calculates a side-by-side diff from a unified diff."""

    def __init__(self, unified_diff, diffon=DIFFON, diffoff=DIFFOFF):
        self.unified_diff = unified_diff
        self.diffon = diffon
        self.diffoff = diffoff
        self.reset()

    def reset(self):
        self.buf = []
        self.add_cpt = 0
        self.del_cpt = 0
        self.line1 = 0
        self.line2 = 0
        self.hunk_off1 = 0
        self.hunk_size1 = 0
        self.hunk_off2 = 0
        self.hunk_size2 = 0
        self._bytes_processed = 0

    @property
    def bytes_processed(self):
        return self._bytes_processed

    def empty_buffer(self):
        if self.del_cpt == 0 or self.add_cpt == 0:
            for l in self.buf:
                yield from self.yield_line(l[0], l[1])

        elif self.del_cpt != 0 and self.add_cpt != 0:
            l0, l1 = [], []
            for l in self.buf:
                if l[0] is not None:
                    l0.append(l[0])
                if l[1] is not None:
                    l1.append(l[1])
            max_len = (len(l0) > len(l1)) and len(l0) or len(l1)
            for i in range(max_len):
                s0, s1 = "", ""
                if i < len(l0):
                    s0 = l0[i]
                if i < len(l1):
                    s1 = l1[i]
                yield from self.yield_line(s0, s1)

    def yield_line(self, s1, s2):
        orig1 = s1
        orig2 = s2

        if s1 is None and s2 is None:
            type_name = "unmodified"
        elif s1 == "" and s2 == "":
            type_name = "unmodified"
        elif s1 is None or s1 == "":
            type_name = "added"
        elif s2 is None or s2 == "":
            type_name = "deleted"
        elif (
            orig1 == orig2
            and not s1.endswith('lines removed ]')
            and not s2.endswith('lines removed ]')
        ):
            type_name = "unmodified"
        else:
            type_name = "changed"
            s1, s2 = linediff(s1, s2, self.diffon, self.diffoff)

        yield "L", (type_name, s1, self.line1, s2, self.line2)

        m = orig1 and re.match(r"^\[ (\d+) lines removed \]$", orig1)
        if m:
            self.line1 += int(m.group(1))
        elif orig1:
            self.line1 += 1
        m = orig2 and re.match(r"^\[ (\d+) lines removed \]$", orig2)
        if m:
            self.line2 += int(m.group(1))
        elif orig2:
            self.line2 += 1

        self.add_cpt = 0
        self.del_cpt = 0
        self.buf = []

    def items(self):
        """Yield the items that form the side-by-side diff.

        Each item is a (type, value) tuple, as follows:

        type == "H", value is a tuple representing a hunk header
            hunk_offset1, hunk_size1, hunk_offset2, hunk_size2 = value
            all ints

        type == "L", value is a tuple representing a line of a hunk
            mode, line1, lineno1, line2, lineno2 = value
            where mode is one of {"unmodified", "added", "deleted", "changed"}
            line* are strings
            lineno* are ints

        type == "C", value is a comment
            comment = value
            a string
        """
        self.reset()

        for l in diff_split_lines(self.unified_diff, False):
            self._bytes_processed += len(l) + 1
            m = re.match(r'^--- ([^\s]*)', l)
            if m:
                yield from self.empty_buffer()
                continue
            m = re.match(r'^\+\+\+ ([^\s]*)', l)
            if m:
                yield from self.empty_buffer()
                continue

            m = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*)", l)
            if m:
                yield from self.empty_buffer()
                hunk_data = map(lambda x: x == "" and 1 or int(x), m.groups())
                self.hunk_off1, self.hunk_size1, self.hunk_off2, self.hunk_size2 = (
                    hunk_data
                )
                self.line1, self.line2 = self.hunk_off1, self.hunk_off2
                yield "H", (
                    self.hunk_off1,
                    self.hunk_size1,
                    self.hunk_off2,
                    self.hunk_size2,
                )
                continue

            if re.match(r'^\[', l):
                yield from self.empty_buffer()
                yield "C", l

            if re.match(r"^\\ No newline", l):
                if self.hunk_size2 == 0:
                    self.buf[-1] = (
                        self.buf[-1][0],
                        self.buf[-1][1] + '\n' + l[2:],
                    )
                else:
                    self.buf[-1] = (
                        self.buf[-1][0] + '\n' + l[2:],
                        self.buf[-1][1],
                    )
                continue

            if self.hunk_size1 <= 0 and self.hunk_size2 <= 0:
                yield from self.empty_buffer()
                continue

            m = re.match(r"^\+\[ (\d+) lines removed \]$", l)
            if m:
                self.add_cpt += int(m.group(1))
                self.hunk_size2 -= int(m.group(1))
                self.buf.append((None, l[1:]))
                continue

            if re.match(r"^\+", l):
                self.add_cpt += 1
                self.hunk_size2 -= 1
                self.buf.append((None, l[1:]))
                continue

            m = re.match(r"^-\[ (\d+) lines removed \]$", l)
            if m:
                self.del_cpt += int(m.group(1))
                self.hunk_size1 -= int(m.group(1))
                self.buf.append((l[1:], None))
                continue

            if re.match(r"^-", l):
                self.del_cpt += 1
                self.hunk_size1 -= 1
                self.buf.append((l[1:], None))
                continue

            if re.match(r"^ ", l) and self.hunk_size1 and self.hunk_size2:
                yield from self.empty_buffer()
                self.hunk_size1 -= 1
                self.hunk_size2 -= 1
                self.buf.append((l[1:], l[1:]))
                continue

            yield from self.empty_buffer()

        yield from self.empty_buffer()
