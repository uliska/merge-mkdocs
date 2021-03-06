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
Implement books as parts of a multi-book documentation site.
"""


import os
import oyaml

from subprocess import Popen

from .util import (
    read_yaml,
    missing_file,
    serialize_yaml
)


MKDOCS_HEADER_COMMENT = """### This book configuration file is generated by mkdocs-library
### Do not edit this file.
### Please refer to the documentation for details

"""


class AbstractBook(object):
    """Represents a book.
    Books are part of a mkdocs-library multi-book site.
    """

    def __init__(self, project, name):

        self._project = project
        self._name = name
        self._src_root = root = os.path.join(
            project.root(),
            'books',
            name
        )
        self._target_file = os.path.join(
            root,
            'mkdocs.yml'
        )
        self._site_root = os.path.join(
            project.root(),
            project.config('site_root'),
            self.site_segment()
        )
        config_dir = os.path.join(
            root,
            '_config'
        )
        config_file = os.path.join(
            config_dir,
            'book-config.yml'
        )
        nav_file = os.path.join(
            config_dir,
            'navigation.yml'
        )
        if not os.path.exists(nav_file):
            missing_file(self._name)
        self._config = read_yaml(config_file)
        self._config['src_dir'] = 'books/{}'.format(self._name)
        self._common = ''
    # TODO:
    # https://github.com/uliska/mkdocs-library/issues/1
        self._nav = {
            'nav': read_yaml(nav_file)
        }
        self._search_index = None
        self._built = False

    def book_config(self, key):
        """Returns a configuration variable on book level,
        or None, if not defined.
        Should only be called from Project.config().
        """
        return self._config.get(key, None)

    def build(self):
        """Call MkDocs to build the book."""
        print("Building partial book", self.name())
        print()
        p = Popen(['mkdocs', 'build'], cwd=self.src_root())
        p.wait()
        output, errors = p.communicate()
        print(output)
        if errors:
            raise Exception(errors)
        print("\n=======\n")
        self._built = True

    def common(self, serialized=False):
        """The common part of a mkdocs.yml file."""
        return serialize_yaml(self._common) if serialized else self._common

    def config(self, key):
        """The configuration dictionary."""
        return self.project().config(key, self)

    def is_main_book(self):
        """Return True if this is a main book, False for a sub book."""
        return isinstance(self, MainBook)

    def link_text(self):
        """Return the link text used for this book."""
        return self.title()

    def name(self):
        """The book 'name' (i.e. the path segment addressing it)"""
        return self._name

    def nav(self, serialized=False):
        """Return the navigation configuration.
        Either a reference to the internal dictionary
        or as a serialized multiline string.
        """
        return serialize_yaml(self._nav) if serialized else self._nav

    def project(self):
        """Reference to the parent project."""
        return self._project

    def search_index(self):
        """A (generated) search index.
        This is generated by MkDocs and will be updated in the process.
        The object will be created upon first request.
        """
        if not self._search_index:
            from .indexes import SearchIndex
            self._search_index = SearchIndex(self)

        return self._search_index

    def set_nav(self, navigation):
        if type(navigation) == str:
            self._nav = oyaml.load(navigation)
            if not 'nav' in self._nav:
                self._nav = {
                    'nav': self._nav
                }
        else:
            self._nav = navigation

    def site_root(self):
        """The root directory of the rendered HTML book."""
        return self._site_root

    def src_root(self):
        """The root directory of the Markdown sources."""
        return self._src_root

    def target_file(self):
        """The mkdocs.yml file where the generated configuration is stored."""
        return self._target_file

    def title(self):
        """The (visible) title of the sub book."""
        return self.config('book_name')

    def update_template(self):
        """
        Update the template with actual values.
        """

        template = self.project().template()
        for item in self.project().defaults():
            # TODO: In order to make this work the 'src_dir' "default"
            # is added to the project defaults dictionary.
            # This approach is convoluted and intransparent and should be fixed.
            # And the edit_uri handling has to be considered with regard to
            # the "known" providers where it will currently probably fail to
            # insert the books/<<<src_dir>>> part.
            template = template.replace(
                '<<<{}>>>'.format(item),
                self.config(item) or self.project().defaults(item)
            )

        self._common = result = oyaml.load(template, Loader=oyaml.SafeLoader)

        # Calculate the relative directory where the book will be rendered to
        result['site_name'] = self.config('book_name')
        result['site_dir'] = '../../{root}{path}'.format(
            root = self.config('site_root'),
            path = self.site_path()
        )

    def use_tabs(self):
        """Return True if the book uses Material's tabs feature."""
        return self.common().get(
            'theme', {}
        ).get(
            'feature', {}
        ).get('tabs', False)

    def write_yaml(self):
        """Write the generated content to a file."""
        content = (
            MKDOCS_HEADER_COMMENT
            + self.common(serialized=True)
            + self.nav(serialized=True)
        )

        with open(self.target_file(), 'w') as f:
            f.write(content)


class MainBook(AbstractBook):
    """Represents the main book on a site."""

    def link_text(self):
        """Returns the link text to be used in a 'home' link.
        Should be customized in the project's config.yml."""
        return self.config('library_link_text') or self.title()

    def site_path(self):
        return ''

    def site_segment(self):
        return ''


class SubBook(AbstractBook):
    """Represents a sub book on a site.
    Differs from a main book only in its addressing
    scheme in the rendered site.
    """

    def site_path(self):
        # TODO: Make this configurable (for arbitrary nesting of subbooks)
        # https://github.com/uliska/mkdocs-library/issues/14
        return '/{}'.format(self.name())

    def site_segment(self):
        # TODO: Has to match the site_path if that is changed
        return self.name()
