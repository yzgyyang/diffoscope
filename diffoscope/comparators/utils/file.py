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

import os
import re
import abc
import magic
import logging
import subprocess

from diffoscope.exc import (
    RequiredToolNotFound,
    OutputParsingError,
    ContainerExtractionError,
)
from diffoscope.tools import tool_required
from diffoscope.config import Config
from diffoscope.profiling import profile
from diffoscope.difference import Difference

try:
    import tlsh
except ImportError:  # noqa
    tlsh = None

SMALL_FILE_THRESHOLD = 65536  # 64 kiB

logger = logging.getLogger(__name__)


def path_apparent_size(path=".", visited=None):
    # should output the same as `du --apparent-size -bs "$path"`
    if not visited:
        stat = os.stat(path, follow_symlinks=False)
        visited = {stat.st_ino: stat.st_size}
    if os.path.isdir(path) and not os.path.islink(path):
        for entry in os.scandir(path):
            inode = entry.inode()
            if inode in visited:
                continue
            visited[inode] = entry.stat(follow_symlinks=False).st_size
            if entry.is_dir(follow_symlinks=False):
                path_apparent_size(entry.path, visited)
    return sum(visited.values())


def _run_tests(fold, tests):
    return fold(t(y, x) for x, t, y in tests)


class File(object, metaclass=abc.ABCMeta):
    if hasattr(magic, 'open'):  # use Magic-file-extensions from file

        @classmethod
        def guess_file_type(self, path):
            if not hasattr(self, '_mimedb'):
                self._mimedb = magic.open(magic.NONE)
                self._mimedb.load()
            return self._mimedb.file(
                path.encode('utf-8', errors='surrogateescape')
            )

        @classmethod
        def guess_encoding(self, path):
            if not hasattr(self, '_mimedb_encoding'):
                self._mimedb_encoding = magic.open(magic.MAGIC_MIME_ENCODING)
                self._mimedb_encoding.load()
            return self._mimedb_encoding.file(path)

    else:  # use python-magic

        @classmethod
        def guess_file_type(self, path):
            if not hasattr(self, '_mimedb'):
                self._mimedb = magic.Magic()
            return maybe_decode(self._mimedb.from_file(path))

        @classmethod
        def guess_encoding(self, path):
            if not hasattr(self, '_mimedb_encoding'):
                self._mimedb_encoding = magic.Magic(mime_encoding=True)
            return maybe_decode(self._mimedb_encoding.from_file(path))

    def __init__(self, container=None):
        self._container = container

    def __repr__(self):
        return '<%s %s>' % (self.__class__, self.name)

    # This should return a path that allows to access the file content
    @property
    @abc.abstractmethod
    def path(self):
        raise NotImplementedError()

    # Remove any temporary data associated with the file. The function
    # should be idempotent and work during the destructor.
    def cleanup(self):
        if hasattr(self, '_as_container'):
            del self._as_container

    def __del__(self):
        self.cleanup()

    FILE_EXTENSION_SUFFIX = None
    FILE_TYPE_RE = None
    FILE_TYPE_HEADER_PREFIX = None

    @classmethod
    def recognizes(cls, file):
        """Check if a file's type matches the one represented by this class.

        The default test returns True if the file matches these tests:

        (cls.FILE_TYPE_RE OR
         cls.FILE_TYPE_HEADER_PREFIX) AND
        (cls.FILE_EXTENSION_SUFFIX)

        If any test is None then the test is ignored and effectively deleted
        from the above definition.

        By default, the tests are all None and the test returns False for all
        files. Subclasses may override them with specific values, or override
        this method to implement a totally different test.
        """
        # The structure below allows us to construct a boolean tree of tests
        # that can be combined with all() and any(). Tests that are not defined
        # for a class are filtered out, so that we don't get into a "vacuous
        # truth" situation like a naive all([]) invocation would give.

        file_type_tests = [
            test
            for test in (
                (
                    cls.FILE_TYPE_RE,
                    lambda m, t: t.search(m),
                    file.magic_file_type,
                ),
                (
                    cls.FILE_TYPE_HEADER_PREFIX,
                    bytes.startswith,
                    file.file_header,
                ),
            )
            if test[0]
        ]  # filter out undefined tests

        all_tests = [
            test
            for test in (
                (cls.FILE_EXTENSION_SUFFIX, str.endswith, file.name),
                (file_type_tests, _run_tests, any),
            )
            if test[0]
        ]  # filter out undefined tests, inc. file_type_tests if it's empty

        return _run_tests(all, all_tests) if all_tests else False

    ENABLE_FALLBACK_RECOGONIZES = True
    FALLBACK_FILE_EXTENSION_SUFFIX = None
    FALLBACK_FILE_TYPE_HEADER_PREFIX = None

    @classmethod
    def fallback_recognizes(cls, file):
        """This is checked if the file could not be identified by recognizes().
        This helps to work around bugs in file(1), see Debian bug #876316.

        The default test returns True if the file matches these tests:

        (cls.FALLBACK_FILE_EXTENSION_SUFFIX AND cls.FILE_EXTENSION_SUFFIX) AND
        (cls.FALLBACK_FILE_TYPE_HEADER_PREFIX AND cls.FILE_TYPE_HEADER_PREFIX)

        We also AND-compare with the non-fallback versions to ensure that
        subclasses don't "accidentally match" (e.g. IpkFile vs GzipFile).
        """
        if cls.recognizes.__func__ != File.recognizes.__func__:
            # If the class has overridden the default recognizes() then the
            # logic below about AND-comparing with the non-fallback versions is
            # not valid, they have to re-implement it
            return False

        if not cls.ENABLE_FALLBACK_RECOGONIZES:
            return False

        all_tests = [
            test
            for test in (
                (cls.FALLBACK_FILE_EXTENSION_SUFFIX, str.endswith, file.name),
                (cls.FILE_EXTENSION_SUFFIX, str.endswith, file.name),
                (
                    cls.FALLBACK_FILE_TYPE_HEADER_PREFIX,
                    bytes.startswith,
                    file.file_header,
                ),
                (
                    cls.FILE_TYPE_HEADER_PREFIX,
                    bytes.startswith,
                    file.file_header,
                ),
            )
            if test[0]
        ]  # filter out undefined tests, inc. file_type_tests if it's empty

        return _run_tests(all, all_tests) if all_tests else False

    # This might be different from path and is used to do file extension matching
    @property
    def name(self):
        return self._name

    @property
    def container(self):
        return self._container

    @property
    def as_container(self):
        if not hasattr(self.__class__, 'CONTAINER_CLASS'):
            if hasattr(self, '_other_file'):
                return self._other_file.__class__.CONTAINER_CLASS(self)
            return None
        if not hasattr(self, '_as_container'):
            logger.debug(
                'instantiating %s for %s', self.__class__.CONTAINER_CLASS, self
            )
            try:
                self._as_container = self.__class__.CONTAINER_CLASS(self)
            except RequiredToolNotFound:
                return None
        logger.debug(
            "Returning a %s for %s",
            self._as_container.__class__.__name__,
            self,
        )
        return self._as_container

    @property
    def progress_name(self):
        x = self._name

        return x[1:] if x.startswith('./') else x

    @property
    def magic_file_type(self):
        if not hasattr(self, '_magic_file_type'):
            self._magic_file_type = File.guess_file_type(self.path)
        return self._magic_file_type

    @property
    def file_header(self):
        if not hasattr(self, '_file_header'):
            with open(self.path, 'rb') as f:
                self._file_header = f.read(16)
        return self._file_header

    @property
    def file_type(self):
        for x, y in (
            (self.is_device, "device"),
            (self.is_symlink, "symlink"),
            (self.is_directory, "directory"),
        ):
            if x():
                return y

        return "file"

    if tlsh:

        @property
        def fuzzy_hash(self):
            if not hasattr(self, '_fuzzy_hash'):
                # tlsh is not meaningful with files smaller than 512 bytes
                if os.stat(self.path).st_size >= 512:
                    h = tlsh.Tlsh()
                    with open(self.path, 'rb') as f:
                        for buf in iter(lambda: f.read(32768), b''):
                            h.update(buf)
                    h.final()
                    try:
                        self._fuzzy_hash = h.hexdigest()
                    except ValueError:
                        # File must contain a certain amount of randomness.
                        self._fuzzy_hash = None
                else:
                    self._fuzzy_hash = None
            return self._fuzzy_hash

    @abc.abstractmethod
    def is_directory():
        raise NotImplementedError()

    @abc.abstractmethod
    def is_symlink():
        raise NotImplementedError()

    @abc.abstractmethod
    def is_device():
        raise NotImplementedError()

    def compare_bytes(self, other, source=None):
        from .compare import compare_binary_files

        # Don't attempt to compare directories with any other type as binaries
        if os.path.isdir(self.path) or os.path.isdir(other.path):
            return Difference.from_text(
                "type: {}".format(self.file_type),
                "type: {}".format(other.file_type),
                self.name,
                other.name,
                source,
            )

        return compare_binary_files(self, other, source)

    def _compare_using_details(self, other, source):
        details = []
        difference = Difference(None, self.name, other.name, source=source)

        if hasattr(self, 'compare_details'):
            details.extend(self.compare_details(other, source))
        if self.as_container:
            if self.as_container.auto_diff_metadata:
                details.extend(
                    [
                        Difference.from_text(
                            self.magic_file_type,
                            other.magic_file_type,
                            self,
                            other,
                            source='filetype from file(1)',
                        ),
                        Difference.from_text(
                            self.__class__.__name__,
                            other.__class__.__name__,
                            self,
                            other,
                            source='filetype from diffoscope',
                        ),
                    ]
                )
            # Don't recurse forever on archive quines, etc.
            depth = self._as_container.depth
            no_recurse = depth >= Config().max_container_depth
            if no_recurse:
                msg = "Reached max container depth ({})".format(depth)
                logger.debug(msg)
                difference.add_comment(msg)
            details.extend(
                self.as_container.compare(
                    other.as_container, no_recurse=no_recurse
                )
            )

        details = [x for x in details if x]
        if not details:
            return None
        difference.add_details(details)

        return difference

    def has_same_content_as(self, other):
        logger.debug('File.has_same_content: %s %s', self, other)
        if os.path.isdir(self.path) or os.path.isdir(other.path):
            return False
        # try comparing small files directly first
        try:
            my_size = os.path.getsize(self.path)
            other_size = os.path.getsize(other.path)
        except OSError:
            # files not readable (e.g. broken symlinks) or something else,
            # just assume they are different
            return False
        if my_size == other_size and my_size <= SMALL_FILE_THRESHOLD:
            try:
                with profile('command', 'cmp (internal)'):
                    with open(self.path, 'rb') as file1, open(
                        other.path, 'rb'
                    ) as file2:
                        return file1.read() == file2.read()
            except OSError:
                # one or both files could not be opened for some reason,
                # assume they are different
                return False

        return self.cmp_external(other)

    @tool_required('cmp')
    def cmp_external(self, other):
        return (
            subprocess.call(
                ('cmp', '-s', self.path, other.path),
                shell=False,
                close_fds=True,
            )
            == 0
        )

    # To be specialized directly, or by implementing compare_details
    def compare(self, other, source=None):
        if hasattr(self, 'compare_details') or self.as_container:
            try:
                difference = self._compare_using_details(other, source)
                # no differences detected inside? let's at least do a binary diff
                if difference is None:
                    difference = self.compare_bytes(other, source=source)
                    if difference is None:
                        return None
                    try:
                        infix = type(self).DESCRIPTION
                    except AttributeError:
                        infix = 'this file format'
                    suffix = ''
                    if self.magic_file_type != 'data':
                        suffix = ' file(1) reports: {}'.format(
                            self.magic_file_type
                        )
                    difference.add_comment(
                        "Format-specific differences are supported for {} but "
                        "no file-specific differences were detected; falling "
                        "back to a binary diff.{}".format(infix, suffix)
                    )
            except subprocess.CalledProcessError as e:
                difference = self.compare_bytes(other, source=source)
                if e.output:
                    output = re.sub(r'^', '    ', e.output, flags=re.MULTILINE)
                else:
                    output = '<none>'
                cmd = ' '.join(e.cmd)
                if difference is None:
                    return None
                difference.add_comment(
                    "Command `%s` exited with %d. Output:\n%s"
                    % (cmd, e.returncode, output)
                )
            except RequiredToolNotFound as e:
                difference = self.compare_bytes(other, source=source)
                if difference is None:
                    return None
                difference.add_comment(
                    "'%s' not available in path. Falling back to binary comparison."
                    % e.command
                )
                package = e.get_package()
                if package:
                    difference.add_comment(
                        "Install '%s' to get a better output." % package
                    )
            except OutputParsingError as e:
                difference = self.compare_bytes(other, source=source)
                if difference is None:
                    return None
                difference.add_comment(
                    "Error parsing output of `%s` for %s"
                    % (e.command, e.object_class)
                )
            except ContainerExtractionError as e:
                difference = self.compare_bytes(other, source=source)
                if difference is None:
                    return None
                difference.add_comment(
                    "Error extracting '{}', falling back to "
                    "binary comparison ('{}')".format(
                        e.pathname, e.wrapped_exc
                    )
                )
            return difference
        return self.compare_bytes(other, source)


def maybe_decode(s):
    """
    Helper function to convert to bytes if necessary.
    """

    if type(s) is bytes:
        return s.decode('utf-8')
    return s
