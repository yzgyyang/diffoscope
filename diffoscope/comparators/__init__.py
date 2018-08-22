# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#           ©      2015  Helmut Grohne <helmut@subdivi.de>
#           ©      2017  Chris Lamb <lamby@debian.org>
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

import sys
import logging
import importlib
import traceback

from ..logging import line_eraser


logger = logging.getLogger(__name__)


class ComparatorManager(object):
    COMPARATORS = (
        ('directory.Directory',),
        ('missing_file.MissingFile',),
        ('symlink.Symlink',),
        ('device.Device',),
        ('debian.DotChangesFile', 'debian_fallback.DotChangesFile'),
        ('debian.DotDscFile', 'debian_fallback.DotDscFile'),
        ('debian.DotBuildinfoFile', 'debian_fallback.DotBuildinfoFile'),
        ('deb.Md5sumsFile',),
        ('deb.DebDataTarFile',),
        ('elf.ElfSection',),
        ('binwalk.BinwalkFile',),
        ('ps.PsFile',),
        ('javascript.JavaScriptFile',),
        ('json.JSONFile',),
        ('xml.XMLFile',),
        ('text.TextFile',),
        ('bzip2.Bzip2File',),
        ('cpio.CpioFile',),
        ('deb.DebFile',),
        ('dex.DexFile',),
        ('elf.ElfFile',),
        ('macho.MachoFile',),
        ('fsimage.FsImageFile',),
        ('elf.StaticLibFile',),
        ('llvm.LlvmBitCodeFile',),
        ('sqlite.Sqlite3Database',),
        ('fonts.TtfFile',),
        ('fontconfig.FontconfigCacheFile',),
        ('gettext.MoFile',),
        ('ipk.IpkFile',),
        ('rust.RustObjectFile',),
        ('gnumeric.GnumericFile',),
        ('gzip.GzipFile',),
        ('haskell.HiFile',),
        ('icc.IccFile',),
        ('iso9660.Iso9660File',),
        ('java.ClassFile',),
        ('lz4.Lz4File',),
        ('mono.MonoExeFile',),
        ('pdf.PdfFile',),
        ('png.PngFile',),
        ('ppu.PpuFile',),
        ('rdata.RdbFile',),
        ('rdata.RdsFile',),
        ('rpm.RpmFile', 'rpm_fallback.RpmFile'),
        ('squashfs.SquashfsFile',),
        ('ar.ArFile',),
        ('tar.TarFile',),
        ('xz.XzFile',),
        ('apk.ApkFile',),
        ('odt.OdtFile',),
        ('docx.DocxFile',),
        ('zip.ZipFile',),
        ('zip.MozillaZipFile',),
        ('image.JPEGImageFile',),
        ('image.ICOImageFile',),
        ('cbfs.CbfsFile',),
        ('git.GitIndexFile',),
        ('android.AndroidBootImgFile',),
        ('openssh.PublicKeyFile',),
        ('gif.GifFile',),
        ('pcap.PcapFile',),
        ('pgp.PgpFile',),
        ('dtb.DeviceTreeFile',),
        ('ogg.OggFile',),
        ('xsb.XsbFile',),
        ('berkeley_db.BerkeleyDBFile',),
    )

    _singleton = {}

    def __init__(self):
        self.__dict__ = self._singleton

        if not self._singleton:
            self.reload()

    def reload(self):
        self.classes = []

        for xs in self.COMPARATORS:
            errors = []
            for x in xs:
                package, klass_name = x.rsplit('.', 1)

                try:
                    mod = importlib.import_module(
                        'diffoscope.comparators.{}'.format(package)
                    )
                except ImportError as e:
                    errors.append((x, e))
                    continue

                self.classes.append(getattr(mod, klass_name))
                break
            else:  # noqa
                logger.error("Could not import {}{}".format(
                    "any of " if len(xs) > 1 else '',
                    ', '.join(xs)
                ))
                for x in errors:
                    logger.error("Original error for %s:", x[0])
                    sys.stderr.buffer.write(line_eraser())
                    traceback.print_exception(None, x[1], x[1].__traceback__)
                sys.exit(2)

        logger.debug("Loaded %d comparator classes", len(self.classes))

    def get_descriptions(self):
        for x in self.classes:
            try:
                yield x.DESCRIPTION
            except AttributeError:
                pass
