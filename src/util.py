# This file is part of the merge-mkdocs project,
# https://github.com/uliska/merge-mkdocs
# https://glarean.mh-freiburg.de/git/GLAREAN-Doku/merge-mkdocs/
#
# Copyright (c) 2020 by Urs Liska
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
        return oyaml.load(f.read(), Loader=oyaml.SafeLoader)
