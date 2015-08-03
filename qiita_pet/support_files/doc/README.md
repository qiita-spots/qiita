Qiita documentation
===================

This guide contains instructions for building the qiita documentation, as well
as guidelines for contributing to the documentation.

Building the documentation
--------------------------

To build the documentation, you'll need the following Python packages
installed:

- [Sphinx](http://sphinx-doc.org/) >= 1.2.2
- [sphinx-bootstrap-theme](https://pypi.python.org/pypi/sphinx-bootstrap-theme/)

An easy way to install the dependencies is via pip:

    pip install Sphinx sphinx-bootstrap-theme

To build the documentation (assuming you have a working installation of Qiita):

    qiita pet webserver

Or alternatively you can (assuming you are at the top-level Qiita folder):

    make -C qiita_pet/support_files/doc html

The built HTML documentation will be at ```build/html/index.html```.

Contributing to the documentation
---------------------------------

Before submitting your changes, ensure that the documentation builds without
any errors or warnings, and that there are no broken links:

    make clean
    make html
    make linkcheck

### When to add a new document?

In general, if you are adding a new feature or modifying an exisiting feature,
you should consider adding a new document or modfiying the pertaining document
so we can keep this information up to date.

### Troubleshooting

If things aren't working correctly, try running ```make clean``` and then
rebuild the docs. If things still aren't working, try building the docs
*without* your changes, and see if there are any Sphinx errors or warnings.
Make note of these, and then see what new errors or warnings are generated when
you add your changes again.
