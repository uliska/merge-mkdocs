# Handling Books
# Part of merge-mkdocs

import os
import sys

from subprocess import Popen

from util import (
    read_yaml,
    missing_file
)


class AbstractBook(object):
    """Partial Book class.
    MainBook and SubBook are very similar but have to be loaded explicitly.
    """

    def __init__(self, project, entry):

        self._project = project
        self._name = entry['name']
        self._title = entry['title']
        self._root = root = os.path.join(project.root(), 'books', self._name)
        self._target_file = os.path.join(root, 'mkdocs.yml')
        config_dir = os.path.join(root, '_merge-mkdocs-config')
        config_file = os.path.join(config_dir, 'book-config.yml')
        nav_file = os.path.join(config_dir, 'navigation.yml')
        if not (
            os.path.exists(root)
            and os.path.exists(config_file)
            and os.path.exists(nav_file)
        ):
            # TODO: Make this better by using defaults
            missing_file(self._name)
        self._config = read_yaml(config_file)
        self._config['src_dir'] = self._name
        self._common = ''
        with open(nav_file, 'r') as f:
            self._nav = f.read().split('\n')

    def build(self):
        """Call MkDocs to build the book."""
        print("Building partial book", self.name())
        print()
        p = Popen(['mkdocs', 'build'], cwd=self.root())
        p.wait()
        output, errors = p.communicate()
        print(output)
        if errors:
            raise Exception(errors)
        print("\n=======\n")


    def config(self):
        return self._config

    def name(self):
        return self._name

    def nav(self):
        return self._nav

    def project(self):
        return self._project

    def root(self):
        return self._root

    def set_common(self, content):
        self._common = content

    def set_nav(self, content):
        self._nav = '\n'.join(content)

    def set_target(self, content):
        self._target = content

    def target_file(self):
        return self._target_file

    def title(self):
        return self._title

    def update_template(self):
        """
        Update the template with actual values.
        """
        result = self.project().template()
        for item in self.project().defaults():
            result = result.replace(
                '<<<{}>>>'.format(item),
                self.config().get(item, None) or self.project().defaults(item)
            )
        result = result.rstrip('\n') + '\n'

        result = result + "site_dir: '../../{root}{path}'\n\n".format(
            root = self.project().config('site_root'),
            path = self.site_path()
        )
        self.set_common(result)

    def write_yaml(self):
        with open(self.target_file(), 'w') as f:
            f.write(self._common + self.nav())

class MainBook(AbstractBook):

    def site_path(self):
        return ''


class SubBook(AbstractBook):

    def site_path(self):
        return '/{}'.format(self.name())
