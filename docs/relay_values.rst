.. _relay_values:

==================
Relay Values
==================

Relay values are a container type for storing variables within an application which may be accessed from multiple
parts of the code. They may be linked to epics variables so that external applications may also access and change them.
They are analogous to the PV type from the pyepics library, but they are only for local control. Like PV types, these values
may also have callbacks registered to notify code that changes have occured to the variable. This allows a natural linkage to
epics process variables so that external applications can change the PV, the PV callback then changes the relay value (RV)
and that triggers a callback in the code.

For that scenario, the layer of indirection provided by using an RV rather than PV doesn't seem necessary, but the indirection
allows the PV to have separate connection management through either pyepics or pcaspy, and RV's provide some additional functionality including:

 * validation functions which can either accept/reject changes or coerce changes. For floats these can be things like range enforcement or rounding to precision. For strings these can check lengths. These also do type checking.
 * Boolean RV's can be composed in logical operations

The pyepics library
