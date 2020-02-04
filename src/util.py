# Common utility functions
# Part of merge-mkdocs

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
        return oyaml.load(f.read(), Loader=oyaml.BaseLoader)
