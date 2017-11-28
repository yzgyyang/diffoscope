diffoscope
==========

.. only:: not manpage

   .. image:: https://badge.fury.io/py/diffoscope.svg
       :target: http://badge.fury.io/py/diffoscope

   .. image:: https://jenkins.debian.net/buildStatus/icon?job=reproducible_diffoscope_from_git_master&plastic=true
      :target: https://jenkins.debian.net/job/reproducible_diffoscope_from_git_master

diffoscope will try to get to the bottom of what makes files or
directories different. It will recursively unpack archives of many kinds
and transform various binary formats into more human readable form to
compare them. It can compare two tarballs, ISO images, or PDF just as
easily.

It can be scripted through error codes, and a report can be produced
with the detected differences. The report can be text or HTML.
When no type of report has been selected, diffoscope defaults
to write a text report on the standard output.

diffoscope was initially started by the "reproducible builds" Debian
project and now being developed as part of the (wider) `“Reproducible
Builds” initiative <https://reproducible-builds.org>`_.  It is meant
to be able to quickly understand why two builds of the same package
produce different outputs. diffoscope was previously named debbindiff.

See the ``COMMAND-LINE EXAMPLES`` section further below to get you
started, as well as more detailed explanations of all the command-line
options. The same information is also available in
``/usr/share/doc/diffoscope/README.rst`` or similar.

.. raw:: manpage

   .\" the below hack gets rid of the python "usage" message in favour of the
   .\" the synopsis we manually defined in doc/$(PACKAGE).h2m.0
   .SS positional arguments:
   .\" end_of_description_header

Exit status
===========

Exit status is 0 if inputs are the same, 1 if different, 2 if trouble.

Command-line examples
=====================

To compare two files in-depth and produce an HTML report, run something like::

    $ bin/diffoscope --html output.html build1.changes build2.changes

diffoscope will exit with 0 if there's no differences and 1 if there
are.

*diffoscope* can also compare non-existent files::

    $ bin/diffoscope /nonexistent archive.zip

To get all possible options, run::

    $ bin/diffoscope --help

If you have enough RAM, you can improve performance by running::

    $ TMPDIR=/run/shm bin/diffoscope very-big-input-0/ very-big-input-1/

By default this allowed to use up half of RAM; for more add something like::

    tmpfs   /run/shm    tmpfs   size=80%    0   0

to your ``/etc/fstab``; see ``man mount`` for details.

External dependencies
=====================

diffoscope requires Python 3 and the following modules available on PyPI:
`libarchive-c <https://pypi.python.org/pypi/libarchive-c>`_,
`python-magic <https://pypi.python.org/pypi/python-magic>`_.

The various comparators rely on external commands being available. To
get a list of them, please run::

    $ bin/diffoscope --list-tools

Contributors
============

Lunar, Reiner Herrmann, Chris Lamb, Mattia Rizzolo, Ximin Luo, Helmut Grohne,
Holger Levsen, Daniel Kahn Gillmor, Paul Gevers, Peter De Wachter, Yasushi
SHOJI, Clemens Lang, Ed Maste, Joachim Breitner, Mike McQuaid. Baptiste
Daroussin, Levente Polyak.

Contact
=======

Please report bugs and send patches through the Debian bug tracking
system against the diffoscope package:
<https://bugs.debian.org/src:diffoscope>

For more instructions, see ``CONTRIBUTING.rst`` in this directory.

Join the users and developers mailing-list:
<https://lists.reproducible-builds.org/listinfo/diffoscope>

diffoscope website is at <https://diffoscope.org/>

License
=======

diffoscope is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

diffoscope is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

See also
========

* `<https://diffoscope.org/>`
* `<https://wiki.debian.org/ReproducibleBuilds>`
