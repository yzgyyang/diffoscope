#!/usr/bin/make -f
# This file is also present in reprotest, please update that as well if you
# make fixes here.

PACKAGE = diffoscope
VERSION = "92"
SED_fix_package_quirks = -e 's,bin/diffoscope,diffoscope,g'

SED_rm_python_usage_msg = -e '/end_of_description_header/,/positional arguments/{d}'
SED_fix_rst2man_quirks = \
  -e 's,^ \\- ,,' \
  -e 's,^\[,\\[char91],g' \
  -e 's,\.TH *"" "" "",,g'
SED_rst2man_output_to_h2m_input = \
  -e 's,\.SH \(.*\),[\1],g' \
  -e 's,\[$(PACKAGE)\],[DESCRIPTION],gi'

all: $(PACKAGE).1

$(PACKAGE).1: $(PACKAGE).h2m ../$(PACKAGE)/__init__.py
	help2man --version-string=$(VERSION) ../bin/$(PACKAGE) -N --include="$<" | \
	  sed $(SED_rm_python_usage_msg) > "$@"

$(PACKAGE).h2m: $(PACKAGE).h2m.0 ../README.rst Makefile
	{ cat $(PACKAGE).h2m.0; cat ../README.rst | \
	  rst2man -q --no-doc-title | \
	  sed $(SED_fix_rst2man_quirks) \
	      $(SED_fix_package_quirks) \
	      $(SED_rst2man_output_to_h2m_input); } > "$@"

.PHONY: clean
clean:
	$(RM) $(PACKAGE).1 $(PACKAGE).h2m
