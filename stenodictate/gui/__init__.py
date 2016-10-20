"""Contains the GUI classes for the app.

Most of the behavior of the app is driven by the GUI classes. They launch the
various behavior, such as importing texts or starting dictation.

The actual layout of the app is in `.ui` files. These are files which Qt
Designer produces. To lay out the form controls all by hand is excessively
tedious, so we use Qt Designer to do it instead. But the behavior of the form
controls is contained in the corresponding .py files.

The `.ui` files are built into `.py` files during compilation. The built files
are named in the form `foo_ui.py`. These files should not be edited manually.

To rebuild the GUI by hand, run `python setup.py build_ui`. More conveniently,
the Makefile targets to launch the app should do this automatically.
"""
