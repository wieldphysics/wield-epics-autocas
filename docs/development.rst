.. _development:


Development
===========

.. _GitHub: http://github.com/mccullerlp/iirrational/

.. _design:

---------------------
Design Considerations
---------------------

Coding Conventions
+++++++++++++++++++

.. _testing:

Testing
--------

Uses py.test for tests.


tox
---

tox aids testing against multiple versions of python in clean environments. To run it::

   $tox

and to run against the full test suite on the system python::

   $tox -e full

The typical build and install distribution does not include the test suite data.

Helpful links
^^^^^^^^^^^^^

 - http://tox.readthedocs.io/en/latest/example/general.html

.. _docs:

-----------------
Building Docs
-----------------

Documentation is written in the powerful, flexible, and standard Python documentation format, `reStructured Text`_.
Documentation builds are powered by the powerful Pocoo project, Sphinx_. The :ref:`API Documentation <api>` is mostly documented inline throughout the module.

The Docs live in ``iirrational/docs``. In order to build them, you will first need to install Sphinx. ::

	$ pip install sphinx
	$ pip install nbsphinx

and optionally (but very helpful) ::

	$ pip install sphinx-autobuild

Then, to build an HTML version of the docs, run the following from the **docs** directory: ::

	$ make html

and for the autoreload, run::

  $ make livehtml

The ``docs/build/html`` directory will then contain an HTML representation of the documentation. When committed to github, readthedocs will automatically build the latest version and host it.

.. _`reStructured Text`: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx.pocoo.org
.. _rst_cheatsheet: https://github.com/ralsina/rst-cheatsheet/blob/master/rst-cheatsheet.rst
.. _rst_primer: http://www.sphinx-doc.org/en/stable/rest.html
.. _rst_code: http://www.sphinx-doc.org/en/stable/markup/code.html
