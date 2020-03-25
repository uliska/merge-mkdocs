from setuptools import setup

setup(
    name='mkdocs-library',
    version='0.1.0',
    packages=['mkdocs_library'],
    url='https://github.com/uliska/mkdocs-library',
    license='GPL',
    author='Urs Liska',
    author_email='git@ursliska.de',
    description='Compose a "Library" of MkDocs partial/sub-books',
    python_requires='>=3.7',
    include_package_data=True,
    install_requires=[
        'mkdocs>=1.1',
        'oyaml',
    ],
    entry_points={
        "console_scripts": [
            "mkdocs-library = mkdocs_library.main:main",
        ],
    },
)
