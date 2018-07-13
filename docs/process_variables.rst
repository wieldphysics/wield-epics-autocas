.. _process_variables:

==================
Process Variables
==================

Hosting or accessing external process variables requires a large number of
settings to properly connect to specific python types. In the process of setting
up process variable specifications, many other useful services related will be
set up

 * logging through a BURT service
   * With extra rapid-prototyping and debugging features `urgentsave_s`
 * setup of listings for LIGO epics DCU configurations
 * Connection monitoring (for externally hosted variables)


Connecting a `relay_value` type is done through the cas_host function available
to CASUser classes. This function will specify the nature of the connection and
default settings for the given variable.

Most of the configurations are type information and some bounds information.
Which will be detailed later.

The first setting to know is the variable interaction type, which specifies how
the local program should interact with the variable as well as prescribes how
other programs should interact. The values are:

.. glossary::
  report

   variable shows calculation results or internal state which cannot be set. If
   it is logged it will be read only. for externally hosted variables if the
   variable value changes from outside the program, it will be logged. If
   internally hosted, the value will be read-only.

  external

   This variable is controlling an external setting. It may be set from outside
   and the program may attempt to set it or read from it. When it is externally
   hosted, the external value will be updated by the local program value upon
   connection to reflect the current setting.

  internal:

   This variable is controlling a setting internal to the program. It may be set
   from outside and the program may attempt to set it or read from it (more
   typically it will read from it). When it is externally hosted, the program
   value will be updated by the external value upon connection.

  setting:

    This value is purely a setting for the program to read from. If externally
    hosted, the program value will be updated by the external value upon
    connection. If the program modifies the relay-value connected to this
    variable, a warning will be raised.

  command:

   This is a command type, which will be interpreted and then reset to a nominal
   value. These can trigger RPC calls, reset errors and things like that. Should
   almost never be BURT'ed unless there should be a trigger on burt effect. In this
   case burt and EDCU settings default to False.


Most settings should try to be `report` or `setting` types as they are the cleanest interfaces. The internal and external types are also available for PV's which are both read and (explicitly) written to by the program.

The program can specify validation function for the process variables which can coerce values. This is an implicit form of writing to the variable and can occur even for "setting" variables. For instance a setting may be changed, but then coerced to being a multiple of some granularity. If this is done the program never sees the intermediate value, and the coerced value is placed into the epics variable to reflect the setting.
