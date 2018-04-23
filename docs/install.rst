.. _install:
Installation
============

.. _installing:

-----------------
Installing IIRrational
-----------------

Distribute & Pip
----------------

The recommended method of installation is through `pip <http://www.pip-installer.org/>`_::

    $ pip install iirrational

or if you are not administrator, you may do a --user install::

    $ pip install iirrational --user

-------------------
Download the Source
-------------------

You can also install IIRrational from source. The latest release (|version|) is available from GitHub.

* git_
* tarball_
* zip_

.. _
Once you have a copy of the source, you can embed it in your Python package, or install it into your site-packages. ::

    $ python setup.py install

To download the full source history from Git, see :ref:`Source Control <scm>`.

.. _git: http://github.com/mccullerlp/iirrational
.. _tarball: http://github.com/mccullerlp/iirrational/tarball/master
.. _zip: http://github.com/mccullerlp/iirrational/zipball/master

to adjust the source and run from the code directory, install via::

    $ python setup.py develop

or better yet, use pip for this and get the dependencies as well::

    $ pip install -e ./

alternatively, add to PYTHONPATH (be sure to also install or add the dependencies)::

    $ export PYTHONPATH="/path/to/iirrational:$PYTHONPATH"

.. warning::
   Installing using setup.py develop will not expose the package to Matlab. Use the PYTHONPATH install instead.


Staying Updated
---------------

The latest version of IIRrational will available at:

* PyPi: http://pypi.python.org/pypi/iirrational/
* GitHub: http://github.com/mccullerlp/iirrational/

When a new version is available, upgrading using::

    $ pip install iirrational --upgrade

.. note:: This can upgrade dependencies such as numpy and scipy as well!
