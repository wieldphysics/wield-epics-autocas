"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import sys
import cas9epics
#from cas9epics.utilities import pprint


class RVTester(cas9epics.CASUser):
    @cas9epics.dproperty
    def rv_test_float(self):
        rv = cas9epics.RelayValueFloat(0)
        self.cas_host(
            rv, 'VAL',
            unit  = 'seconds',
            interaction = "setting",
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST_FLOAT({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv

    @cas9epics.dproperty
    def rv_test_str(self):
        rv = cas9epics.RelayValueString('hello')
        self.cas_host(
            rv, 'STR',
            interaction = "setting",
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST_STRING({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv

    @cas9epics.dproperty
    def rv_test_long_str(self):
        rv = cas9epics.RelayValueLongString('hello')
        self.cas_host(
            rv, 'STRL',
            interaction = "setting",
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST_LSTRING({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv

    @cas9epics.dproperty
    def rv_test_bool(self):
        rv = cas9epics.RelayBool(False)
        self.cas_host(
            rv, 'BOOL',
            interaction = "setting",
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST_BOOL({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv

    @cas9epics.dproperty
    def rv_test_enum(self):
        rv = cas9epics.RelayValueEnum('A', ['A', 'B', 'C'])
        self.cas_host(
            rv, 'ENUM',
            interaction = "setting",
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST_ENUM({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv


class Testers(cas9epics.CAS9Module):
    @cas9epics.dproperty
    def save(self):
        return RVTester(
            name = 'SAVE',
            parent = self,
        )

if __name__ == "__main__":
    Testers.cmdline(
        module_name_base = 'RVtypes',
    )

