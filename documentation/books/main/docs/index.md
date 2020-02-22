# mkdocs-library: Multi-Book Sites with MkDocs

`mkdocs-library` is an auxiliary program to the
[MkDocs](https://www.mkdocs.org) documentation generator allowing to combine a
set of MkDocs-generated “books” to an integrated “library”.

The basic idea is to have multiple interdependent books that share the same
design and can be parametrically configured. The tool can serve various use
cases (any or multiple of them):

* Add one layer of navigation (especially with the `tabs` feature of the
  [Material](https://squidfunk.github.io/mkdocs-material/) theme).
* Separate parts of a site by consistent design with parametrical differences
  (e.g. colors)
* Encapsulate parts of a site to be maintained in separate repositories by
  different people.

The task that led to the development of this tool was the documentation of
[openLilyLib](https://openlilylib.org), a library of independent packages
extending the [LilyPond](http://lilypond.org) notation software.

This documentation is itself an example of MkDocs and `mkdocs-library`, although in this case it would probably not be necessary to 