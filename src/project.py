#!/usr/bin/env python3

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
Representation of a merge-mkdocs project
"""

import os
import oyaml
import sys

from subprocess import Popen

from book import MainBook, SubBook
from util import read_yaml, missing_file


MKDOCS_HEADER_COMMENT = """
### This book configuration file is generated by merge-mkdocs
### Do not edit this file.
### Please refer to the documentation for details

"""


class Project(object):
    """A merge-mkdocs project, represents a directory structure.
    """

    def __init__(self, cl_args, program_defaults_dir):

        # Project root directory, defaulting to current working directory
        self._root = cl_args.root
        # Directory with the program defaults
        self._program_defaults_dir = program_defaults_dir
        # List of books. If present, the main book is the first in this list.
        self._books = []
        self._has_main_book = False

        # Program and project site configuration files
        config_dir = os.path.join(self._root, '_merge-mkdocs-config')
        self._config_file = os.path.join(config_dir, 'config.yml')
        self._template_file = template_file = os.path.join(
            config_dir, 'template.yml'
        )
        self._defaults_file = defaults_file = os.path.join(
            config_dir, 'defaults.yml'
        )
        self._outline_file = outline_file = os.path.join(
            config_dir, 'outline.yml'
        )

    # TODO: Improve
    # (https://github.com/uliska/merge-mkdocs/issues/2)
        if not (
            os.path.exists(defaults_file)
            and os.path.exists(outline_file)
        ):
            raise Exception("Project, Defaults, or Books file missing")

        # Read and parse the different configuration files
        self._config = self.read_config()
        self._defaults = read_yaml(defaults_file)
    # Hack to make the loop in book.update_template() work
    # TODO: This should better be fixed, I think.
        self._defaults['src_dir'] = ''
        self._template = self.read_template()
        self._books = self.load_books()

        # Decide which recipe is going to be executed
        self._recipe = cl_args.recipe or self.config('default_recipe')

    def book_nav(self, source, target):
        """
        Returns a string list with the navigation entry
        pointing to the given non-home book.
        """
        from_segment = '' if source.is_main_book() else '../'
        to_segment = target.site_segment()
        separator = '' if target.is_main_book() else '/'
        link = '{fr}{to}{sep}index.html'.format(
            fr=from_segment,
            to=to_segment,
            sep=separator
        )

        title = (
            '[{}]'.format(target.link_text())
            if source == target
            else target.link_text()
        )

    # TODO: Clarify how to handle sibling navigation in tabs
    # https://github.com/uliska/merge-mkdocs/issues/8
        return {
            title: link
        }
        # if source.use_tabs():
        #     return {
        #         target.title(): { 'Invisible': link }
        #     }
        # else:
        #     return {
        #         target.title(): link
        #     }

    def books(self):
        """
        Returns a list with all book objects.
        If the project has a main book it will be the first element.
        """
        return self._books

    def config(self, key, book=None):
        """
        Returns a given configuration value defined on
        book, project or program level, in that order.
        If no configuration is available returns None.
        """
        book_config = book.book_config(key) if book else None
        # NOTE: We can't use the 'or' construct to discern between
        # None (no value) and False (valid value)
        if book_config is None:
            book_config = self._config.get(key, None)
        return book_config

    def config_file(self):
        return self._config_file

    def defaults(self, key=None):
        if key:
            return self._defaults[key]
        else:
            return self._defaults

    def exec_recipe(self):
        """Execute a given recipe, i.e. sequence of tasks."""
        recipes = {
            'merge-sources': [
                'task_merge_sources'
            ],
            'build': [
                'task_merge_sources',
                'task_build_site',
                'task_merge_indexes'
            ],
            'merge-indexes': [
                'task_merge_indexes'
            ],
            'deploy': [
                'task_deploy'
            ],
            'all': [
                'task_build_site',
                'task_deploy'
            ]
        }
        recipe = recipes[self.recipe()]
        for step in recipe:
            getattr(self, step)()

    def home_nav(self, from_book):
        """
        Returns a navigation entry to the main book if one exists
        in the project, otherwise None.
        If the book from which this link is created uses the 'tabs'
        feature of the Material theme then a subentry is necessary,
        otherwise a direct link is created.
        """
        main = self.main_book()
        if main:
            if from_book.use_tabs():
                return {
                    main.link_text(): { 'Invisible': '../index.html'}
                }
            else:
                return {
                    main.link_text(): '../index.html'
                }
        else:
            return None

    def load_books(self):
        """Create the book objects."""
    # TODO:
    # https://github.com/uliska/merge-mkdocs/issues/1
        result = []
        outline = read_yaml(self.outline_file())
        if outline[0] == self.config('parent_book'):
            self._has_main_book = True
            result.append(MainBook(self, outline.pop(0)))
        for book in outline:
            # The subbook entries are done different from the main book,
            # so we have to explicitly create the dict here
            result.append(SubBook(self, book))
        return result

    def main_book(self):
        """Return the MainBook object, or None."""
        if self._has_main_book:
            return self.books()[0]
        else:
            return None

    def outline_file(self):
        """The file where the book outline is configured, if present."""
        return self._outline_file

    def read_config(self):
        """
        Read the project's configuration file,
        overriding program defaults with any given value.
        """
        result = read_yaml(os.path.join(
            self._program_defaults_dir,
            'config.yml'
        ))
        config = read_yaml(self.config_file())

        for key, value in config.items():
            result[key] = value

        return result

    def read_template(self):
        """Read the template file."""

    # TODO: Validate against defaults
    # (https://github.com/uliska/merge-mkdocs/issues/2)
        if os.path.exists(self.template_file()):
            with open(self.template_file(), 'r') as f:
                return MKDOCS_HEADER_COMMENT + f.read()
        else:
            return MKDOCS_HEADER_COMMENT

    def recipe(self):
        """The recipe to be performed.
        This can be configured at various levels:
        - value to the command line argument --recipe
          this always takes precedence
        - default_recipe in config.yml
          if this is given it will be used if no --recipe arg is present
        - built-in default_recipe
          lacking *any* user configuration the 'build' recipe is executed
        """
        return self._recipe

    def root(self):
        """The project's root directory.
        Either given on the command line or the current working directory.
        """
        return self._root

    def site_root(self):
        """
        The relative path to the generated site's root.
        Defaults to 'site'.
        """
        return self.config('site_root')

    #################################################
    # High-level implementation of the various tasks.

    def task_build_site(self):
        """Build the site
        Start with the main book because this clears the total site.
        """
        for book in self.books():
            book.build()

    def task_deploy(self):
        """Deploy the site using a user/project-provided script.
        The script can be given as a configuration option, or
        it defaults to 'deploy'. It may be given as relative to
        the project root or as an absolute path.
        The script has to be executable, and it has to work without
        user interaction.
        """
        print("Deploying site")
        script = self.config('deploy_script')
        if not os.path.isabs(script):
            script = os.path.join(self.root(), script)
        p = Popen([script], shell=True)
        p.wait()
        output, errors = p.communicate()
        print(output)
        if errors:
            raise Exception(errors)
        print("\n=======\n")

    def task_merge_indexes(self):
        """Merge search indexes
        MkDocs produces a search index in a JSON file, pointing to
        all documents with links relative to the site's root directory.
        This task enhances these indexes by the indexes of all other books.
        """
        books = self.books()
        # The index objects are initially created in this list comprehension
        indexes = [book.search_index() for book in books]
        for i in indexes:
            # Merge in updated indexes to the other books
            i.update(books)
            # Update JSON file
            i.write()

    def task_merge_sources(self):
        """Preprocess the sources.
        Process templates and navigation files
        for each book.
        """
        for book in self.books():
            # fill in values for template fields
            book.update_template()
            # Generate local navigation and
            # add links to other book parts
            self.update_nav(book)
            # write the book's mkdocs.yml file
            book.write_yaml()

    # High-level implementation of the various tasks.
    #################################################

    def template(self):
        """The template for a mkdocs.yml file.
        This is basically a mkdocs.yml file wtihout the nav: element
        where <<<name>>> template fields can be replaced with values
        from defaults or a book-config.yml file.
        """
        return self._template

    def template_file(self):
        """The project's template file."""
        return self._template_file

    def update_nav(self, book):
        """Process a book's navigation structure.
        Integrate the local navigation in the multi-book set-up.
        NOTE: This modifies the book.nav()['nav'] list in place.
        """
    # TODO: Enhance
    # (https://github.com/uliska/merge-mkdocs/issues/1)
        nav = book.nav()['nav']

        # By default sibling books are *not* linked to
        # because that is somewhat redundant.
        # The default is having the whole navigation structure
        # under control of the subbook and just add the link
        # the the main book.
        if self.config('link_to_siblings', book):
            siblings_position = self.config('siblings_position')

            sibling_nav = {
                self.config('siblings_link_title'): [
                    self.book_nav(book, b)
                    for b in self.books()
                    #if b != book
                ]
            }

            def insert_siblings(nav_branch):
                if siblings_position == 'start':
                    nav_branch.insert(0, sibling_nav)
                else:
                    nav_branch.append(sibling_nav)

            if not book.use_tabs():
                insert_siblings(nav)
            else:
                for i, tl_entry in enumerate(nav):
                    for name, entry in tl_entry.items():
                        if type(entry) != list:
                            entry = [{ name: entry }]
                            nav[i] = { name: entry }
                        insert_siblings(entry)
        # Subbooks get a link to the main book at the top if ...
        elif (
            self.main_book()            # ... there *is* a main book
            and not book.is_main_book() # but it's not the current book
        ):
            nav.insert(0, self.home_nav(book))
