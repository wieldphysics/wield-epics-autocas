.. _quickstart_matlab:

.. module:: iirrational.v1

Quickstart for Matlab
======================

Although this is a python library, it may be used from Matlab via the `builtin (since 2014) python interfaces <https://www.mathworks.com/help/matlab/getting-started-with-python.html>`_

Unfortunately, IIRrational cannot be directly run inside of the Matlab python interpreter. Matlab uses its own library ecosystem, including a number of critical numeric libraries shared by Scipy. At least on linux these are not ABI compatible and python will fail to import many scipy modules due to symbol lookup errors.

A workaround is provided using the `msurrogate <http://msurrogate.readthedocs.io/en/latest/>`_ library, which allows IIRrational to be run as a separate process, while appearing native to Matlab. This not only fixes scipy, but also allows easy multithreaded access and extends the native Matlab python array wrapping conveniently to and from Numpy types.

Installation Steps
--------------------

First :ref:`Install IIRrational through pip <install>` and msurrogate will come with it automatically as a dependency. Now you only need to:

1) check that python is working from Matlab
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See the `Matlab documentation <https://www.mathworks.com/help/matlab/matlab_external/system-and-configuration-requirements.html>`_.

On Linux (Fedora 25) with 2016a, this appears to *just work*, with Matlab finding and using the system python27. If redirected to system python35 matlab fails to find the python libraries. Either it does not support such a new python3 (likely for 2016a as the matlab.engine python module does not support python35). Please submit issues/pull requests to debug this on mac/windows particularly using non-native python distributions such as Anaconda.
     

2) Add IIRrational to matlabpath
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The matlab code to use is stored within the python module (both for IIRrational and msurrogate). To access it, just put it into the path using

.. code-block:: Matlab

    addpath(char(py.iirrational.matlabpath()));

This asks for the path through the python function call matlabpath of the iirrational module. The Matlab `char` function converts from a python string. If this throws an error, then either

 - Python is not found by Matlab
 - IIRrational is not installed, or **not installed into the python environment found by Matlab.** Check which python Matlab found. If you are running from an install from Anaconda, Homebrew, macports et al, then Matlab may not be using the non-system python!


If this is working, then you may either add this code to all projects wishing to use the IIRrational library, or get the paths returned from this function and add them manually to a permanent matlabrc or to MATLABPATH.


Two ways to start
------------------

The separate python process hosting IIRrational communicates with Matlab through sockets. The addresses for this communication are held in a cookie file provided by the python host process. This process must be started with the location to write the cookie file, and then Matlab must be given the location of this file. Using sockets, the python process may even reside on a different computer than Matlab. Since Matlab's python can start this process itself, first try the direct method.

Direct Subprocess Method
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: Matlab
  :emphasize-lines: 1-4

  addpath(char(py.iirrational.matlabpath()));

  %Without arguments, a subprocess is started
  iir = iirrational.surrogate();

  %positional arguments MUST be within a cell array due to
  %the calling convention of the python-wrapping done by msurrogate
  %(they are also discouraged for readability in favor of more verbose keyword arguments)
  dat = iir.testing.iirrational_data({'simple1'});

  %Create native keyword arguments
  kw = struct();
  kw.data = dat.data;
  kw.F_Hz = dat.F_Hz;
  kw.F_nyquist_Hz = dat.F_nyquist_Hz;

  %also add SNR as a keyword arguement
  fit_out = iir.v1.data2filter(kw, 'SNR', dat.SNR);

  %Show the ZPK output to use in other systems
  disp(fit_out.fitter.ZPK)

  %Write a plot
  axB = iir.plots.plot_fitter_flag({fit_out.fitter}, 'fname', 'test_plot.pdf');

This method is convenient as Matlab will manage the lifetime of the subprocess. Furthermore, the stdout (console out) of the python process will be piped into Matlab (although often with a delay).


Separate Process Method
^^^^^^^^^^^^^^^^^^^^^^^^

Use this method if the subprocess method is not working, you would like to manage the lifetime of the python process, or you are running python remotely. You can actually use the system python with Matlab and a newer python environment from the subprocess (perhaps use a virtualenv to get newest scipy/numpy/matplotlib).

Check out the start options with

.. code-block:: bash

    python -m iirrational.matlab -h

and minimally start it using

.. code-block:: bash

    python -m iirrational.matlab -c workspace/path/iirrational.cookie

now inside of matlab

.. code-block:: Matlab

  addpath(char(py.iirrational.matlabpath()));

  %with arguments, a cookie filename to connect to is assumed
  iir = iirrational.surrogate('workspace/path/iirrational.cookie');
  ...


If the process is created on a separate machine, the :option:`--public` option should be given, along with a :option:`--host` hostname (the library is not particularly secure since it transmits using pickle objects, but it does take some minimal steps). The cookie file must be copied to the matlab machine in this case. If the :option:`--port` and :option:`--secret` options are also given, then the cookie file will not change between invocations and the copy is only necessary once.

Usage
-------
The return value of the Matlab `iirrational.surrogate` function is an object representing the proxy workspace. It has a similar structure to the python modules, with a `.v1` attribute providing access to the functions in the python `v1` submodule. It also has `plots` and `annotation`. Tab completion should work for the objects, so try it out to find methods to call and properites to inspect.

Calling Conventions
^^^^^^^^^^^^^^^^^^^^

Function calls are done using the `()` operator from Matlab, wheras item lookup *even into arrays* is done using `{}` operators. If the array was a numpy array it will be converted back into a matlab array and the Matlab `()` indexing syntax will be used. When in doubt, check the return type. `msurrogate.PyWrap` and `msurrogate.PyroWrap` use the python syntax, and otherwise matlab syntax should be assumed. 

Function calling
^^^^^^^^^^^^^^^^^

As alluded in the examples, the function calling syntax is idiosyncratic to conveniently accommodate keyword arguments. The general pattern isempty

.. code-block:: Matlab

   iir.module.function({positional1, positional2, . . .}, kwarg_struct, 'kwarg1', val, 'kwarg2', val, . . .)

And actually any number of cell arrays and kwarg_structs may be used. Positional arg cell arrays are concatenated and kwarg_structs are overlayed, with later ones taking precedence. The first string argument switches the parser to assuming the rest are argname, value pairs and these take the highest precedence. There is no other way to provide positional arguments than through the cell arrays. It is easy to accidentally omit them and hopefully the error messages are helpful.

Gotchas
--------

 - The python subprocess has its own current working directory, so relative paths will NOT be with respect to the current Matlab path, but the python one (likely the directory where matlab was started).
 - Interactive plotting requires `matplotlib to be setup with an appropriate backend. <https://matplotlib.org/faq/usage_faq.html#what-is-a-backend>`_
 - The python workspace currently does not automatically clean up old objects, so it can eat memory if used for an extended period. Garbage collection is planned but not particularly tested
 - in principle, multiple users/workspaces could connect to a single iirrational process. This is untested.
 - Only python lists, tuples, dictionaries and numpy arrays are transmitted. Everything else is a proxy object into the python process. Native types like dicts will be proxies as well if they contain any proxied object.
 - Proxy objects will be "unwrapped" on the python side, so function arguments can be a proxy and python will use the native object in its workspace (good for :class:`MultiReprFilter` objects returned with :func:`data2filter`).

      






.. _matlab_engine: https://www.mathworks.com/help/matlab/matlab-engine-for-python.html
