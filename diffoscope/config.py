# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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


import logging


logger = logging.getLogger(__name__)


class defaultint(int):
    pass


# Avoid setting values on this anywhere other than main.run_diffoscope(),
# otherwise tests may fail unpredictably depending on order-of-execution.
class Config(object):
    _singleton = {}

    def __init__(self):
        self.__dict__ = self._singleton
        if not self._singleton:
            self.reset()

    def reset(self):
        # GNU diff cannot process arbitrary large files :(
        self.max_diff_input_lines = 2 ** 22
        self.max_diff_block_lines_saved = float("inf")

        # hard limits, restricts single-file and multi-file formats
        self.max_report_size = defaultint(40 * 2 ** 20)  # 40 MB
        self.max_diff_block_lines = defaultint(2 ** 10)  # 1024 lines
        # structural limits, restricts single-file formats
        # semi-restricts multi-file formats
        self.max_page_size = defaultint(400 * 2 ** 10)  # 400 kB
        self.max_page_size_child = defaultint(200 * 2 ** 10)  # 200 kB
        self.max_page_diff_block_lines = defaultint(2 ** 7)  # 128 lines

        self.max_text_report_size = 0

        self.new_file = False
        self.fuzzy_threshold = 60
        self.enforce_constraints = True
        self.excludes = ()
        self.exclude_commands = ()
        self.exclude_directory_metadata = 'no'
        self.compute_visual_diffs = False
        self.max_container_depth = 50
        self.use_dbgsym = 'auto'
        self.force_details = False

    def __setattr__(self, k, v):
        super(Config, self).__setattr__(k, v)

    def check_ge(self, a, b):
        va = getattr(self, a)
        vb = getattr(self, b)
        if va < vb:
            if isinstance(vb, defaultint):
                logger.warn(
                    "%s (%s) < default value of %s (%s), setting latter to %s",
                    a,
                    va,
                    b,
                    vb,
                    va,
                )
                setattr(self, b, va)
            else:
                raise ValueError(
                    "{0} ({1}) cannot be smaller than {2} ({3})".format(
                        a, va, b, vb
                    )
                )

    def check_constraints(self):
        self.check_ge("max_diff_block_lines", "max_page_diff_block_lines")
        self.check_ge("max_report_size", "max_page_size")
        self.check_ge("max_report_size", "max_page_size_child")
