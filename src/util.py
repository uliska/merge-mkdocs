# This file is part of the mkdocs-library project,
# https://github.com/uliska/mkdocs-library
# https://glarean.mh-freiburg.de/git/GLAREAN-Doku/mkdocs-library/
#
# Copyright \(c\) 2020 by Urs Liska
# Developed with support of the University of Music Freiburg
# https://mh-freiburg.de
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Common utility functions
"""

import os
import oyaml
import sys

# TODO: This has to become much cleaner
def missing_file(book):
    sys.exit("""
CONFIGURATION ERROR:

Missing conf file in book {}

Aborting.
    """.format(book))


def read_yaml(file):
    """
    Read a YAML file and return its configuration as an ordered dictionary.
    If the file doesn't exist an empty dict is returned.
    """
    if not os.path.exists(file):
        return {}
    with open(file, 'r') as f:
        return oyaml.load(f.read(), Loader=oyaml.SafeLoader) or {}

def serialize_yaml(yml):
    """
    Serialize a YAML dictionary to a multiline string.
    """
    noalias_dumper = oyaml.dumper.SafeDumper
    noalias_dumper.ignore_aliases = lambda self, data: True
    return oyaml.dump(yml, allow_unicode=True, Dumper=noalias_dumper)
