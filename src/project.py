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
Representation of a mkdocs-library project
"""

import os
import re

from subprocess import Popen

from book import MainBook, SubBook
from util import read_yaml


class Project(object):
    """A mkdocs-library project, represents a directory structure.
    """

    def __init__(self, cl_args, program_defaults_dir):

        # Project root directory, defaulting to current working directory
        self._root = cl_args.root
        # Directory with the program defaults
        self._program_defaults_dir = program_defaults_dir
        # List of books.
        self._books = []
        self._main_book = None

        # Project configuration directory
        config_dir = os.path.join(self._root, '_config')
        # Various configuration files
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

        # Store fields found in the project's template file
        self._template_fields = []

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

    def book_nav(self, source, target, tabs=False):
        """
        Returns a nav entry from one to another book.
        Both source and target may be home or a sub-book, although
        a link to itself doesn't make sense.

        If the entry is shown in a tab (Material theme, abs=True)
        there has to be an invisible navigation item, otherwise the
        item is not shown at all.
        """
        from_segment = '' if source.is_main_book() else '../'
        to_segment = target.site_segment()
        separator = '' if target.is_main_book() else '/'
        link = '{fr}{to}{sep}index.html'.format(
            fr=from_segment,
            to=to_segment,
            sep=separator
        )

        # Highlight the link to the current book, at this point with
        # brackets. This should be made configurable.
        # See https://github.com/uliska/mkdocs-library/issues/9
        title = (
            '[{}]'.format(target.link_text())
            if source == target
            else target.link_text()
        )

        if tabs:
            return {
                title: { 'Invisible': link }
            }
        else:
            return {
                title: link
            }

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

    # def library_nav(self, from_book):
    #     """
    #     Returns a navigation entry to the main book if one exists
    #     in the project, otherwise None.
    #     If the book from which this link is created uses the 'tabs'
    #     feature of the Material theme then a subentry is necessary,
    #     otherwise a direct link is created.
    #     """
    #     main = self.main_book()
    #     if main:
    #         if from_book.use_tabs():
    #             return {
    #                 main.link_text(): { 'Invisible': '../index.html'}
    #             }
    #         else:
    #             return {
    #                 main.link_text(): '../index.html'
    #             }
    #     else:
    #         return None

    def load_books(self):
        """Create the book objects.

        The list of books is read either from an outline.yml file
        or from the docs subdirectory.
        In both cases a parent book is created if there is a book
        whose name matches the 'library_book' configuration option.

        If outline.yml is present the parent book is used in the
        list position specified in the file (although usually
        this should be the first position).
        If it is read from disk a parent book is by default placed
        at the start of the list, except the configuration option
        'library_book_at_start' is explicitly set to false.
        """
        result = []
        outline = read_yaml(self.outline_file()) or self.read_outline()
        library_book_name = self.config('library_book')

        for book in outline:
            parent = book == library_book_name
            if parent:
                self._main_book = MainBook(self, book)
                result.append(self._main_book)
            else:
                result.append(SubBook(self, book))
        return result

    def main_book(self):
        """Return the MainBook object, or None."""
        return self._main_book

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

    def read_outline(self):
        """Read book list from books subdirectory.

        This is done when no outline.yml is specified.
        Existing books are read in alphabetical order.
        If the config option 'library_book_at_start' is
        not explicitly set to false a parent book (if
        present) will be moved to the list start.
        """
        books_dir = os.path.join(self.root(), 'books')
        dir_entries = sorted(os.listdir(books_dir))
        books = []
        for entry in dir_entries:
            if os.path.isdir(os.path.join(books_dir, entry)):
                books.append(entry)
        parent_name = self.config('library_book')
        if (
            parent_name
            and parent_name in books
            and books.index(parent_name) > 0
            and self.config('library_book_at_start')
        ):
            books.insert(0, books.pop(books.index(parent_name)))
        return books

    def read_template(self):
        """Read the template file."""

        template = ''
        if os.path.exists(self.template_file()):
            with open(self.template_file(), 'r') as f:
                template += f.read()
        fields = re.findall('<<<.*>>>', template)
        self._template_fields = []
        for field in fields:
            if not field[3:-3] in fields:
                self._template_fields.append(field[3:-3])
        for field in self._template_fields:
            if not field in self.defaults():
                raise Exception("""No default value given for template field
  {field}
in configuration file
  {file}
            """.format(
                field=field,
                file=self._defaults_file
            ))
        return template

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
        books_ordered = [book for book in self.books()]
        parent = self.main_book()
        if parent:
            books_ordered.insert(
                0,
                books_ordered.pop(books_ordered.index(parent)))
        for book in books_ordered:
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
        nav = book.nav()['nav']
        # Get options, determine which links to insert (library/siblings)
        library_link = (
            self.config('link_to_library', book)
            and self.main_book()            # ... there *is* a main book
            and not book.is_main_book() # but it's not the current book
        )
        siblings_link = self.config('link_to_siblings', book)
        siblings_position = self.config('siblings_position')

        # Create a link to the main book
        if library_link:
            main_nav = self.book_nav(
                book,
                self.main_book(),
                tabs=False
            )

        # Create a group of links to the sibling books.
        # The link to the main book is integrated
        # if it is not added standalone.
        sibling_nav = {
            self.config('siblings_link_title'): [
                self.book_nav(book, b)
                for b in self.books()
                if not (
                    b == self.main_book()
                    and self.config('link_to_library', book)
                )
            ]
        }

        def insert_nav(nav_branch):
            """
            Insert main and/or siblings nav links
            into the given navigation branch.
            """
            if siblings_link:
                if siblings_position == 'start':
                    nav_branch.insert(1, sibling_nav)
                else:
                    nav_branch.append(sibling_nav)
            if library_link:
                nav_branch.insert(1, main_nav)

        # Insert detail navigation either in the main
        # navigation bar or into every secondary navigation.
        if not book.use_tabs():
            insert_nav(nav)
        else:
            for i, tl_entry in enumerate(nav):
                for name, entry in tl_entry.items():
                    if type(entry) != list:
                        entry = [{ name: entry }]
                        nav[i] = { name: entry }
                    insert_nav(entry)
