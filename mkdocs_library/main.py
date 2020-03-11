#!/usr/bin/env python3

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
Merge several MkDocs "books" to one multi-book "library".
This is the script's entry file.
"""

import argparse
import os

from .project import Project


def parse_args():
    parser = argparse.ArgumentParser()
    # Recipe controlling what the script actually does.
    # - command line argument takes precedence
    # - default recipe is 'build'
    # - project specific default can be given in the config
    parser.add_argument(
        '--recipe',
        choices=['merge-sources', 'merge-indexes', 'build', 'deploy', 'all'],
        help='Task (sequence) to be performed. Defaults to "build"'
    )
    parser.add_argument(
        '-r', '--root',
        default=os.getcwd(),
        help='Project root directory, defaults to current working directory'
    )
    return parser.parse_args()


def main():
    # Determine the directory with the program defaults
    config_dir = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ),
        'defaults'
    )
    Project(parse_args(), config_dir).exec_recipe()


if __name__ == '__main__':
    main()
