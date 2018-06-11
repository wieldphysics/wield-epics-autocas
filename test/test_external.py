"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import sys
import cas9epics
import declarative
from cas9epics.utilities import pprint
from cas9epics.subservices.restart_on_edit import RestartOnEdit


class RVExternals(cas9epics.CASUser):
    @declarative.dproperty
    def rv_internal(self):
        rv = cas9epics.RelayValueFloat(0)
        self.cas_host(
            rv, 'INT',
            external = False,
            writable = True,
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv

    @declarative.dproperty
    def rv_test(self):
        rv = cas9epics.RelayValueFloat(0)
        self.cas_host(
            rv, 'EXT',
            prefix = ['ISC', 'ADC28', 'GAIN'],
            external = True,
            writable = True,
            urgentsave = 0.1,
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv


class Testers(cas9epics.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVExternals(
            name = 'TEST',
            parent = self,
        )

if __name__ == "__main__":
    Testers.cmdline(
        module_name_base = 'RVExternal',
    )

