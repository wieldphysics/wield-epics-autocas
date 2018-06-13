.. _index:

CAS9Epics
==========

unified epics hosting, channel-access, backup/restore, and configuration
--------------------------------------------------------------------------

This library fuses pcaspy and pyepics and provides a common interface for creating python epics applications.
To list what this library does:
 * handles and encapsulates epics threading issues of both libraries so that programs need no concern for locks.
 * provides programming services such as an event loop and scheduler for tasks to monitor and update process variables.
   * Programming may be either reactive (callback-based) or procedural (regularly scheduled task) or a mixture (tasks modified schedules).
 * Configures both internal settings and all process variables
   * Allowing very hierarchical development, one calibration interface may become N, with each one getting independent, configurable settings and channel names
 * Introspection of configuration
   * current settings may easily be compared against defaults



Contents
------------

.. toctree::
   :maxdepth: 2

   quickstart
   relay_values
   process_variables

Related Projects
------------------


* pyepics http://cars9.uchicago.edu/software/python/pyepics3/pv.html
* pcaspy https://pcaspy.readthedocs.io/en/latest/
* guardian https://dcc.ligo.org/LIGO-G1400016/public
