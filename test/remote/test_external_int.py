"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import sys
import cas9epics
import declarative


class RVConnects(cas9epics.CASUser):
    remote = False
    @declarative.dproperty
    def rv_fl(self):
        rv = cas9epics.RelayValueFloat(0)
        self.cas_host(
            rv, 'FL',
            remote = self.remote,
            interaction = 'internal',
        )

        def cb(value):
            print("RV_FL({0}): ".format(self.name), value)

        rv.register(callback = cb, key = self)

        if not self.remote:
            def update():
                rv.value += .1
            self.reactor.enqueue_looping(update, period_s = .1)
        return rv

    #@declarative.dproperty
    #def rv_int(self):
    #    rv = cas9epics.RelayValueInt(0)
    #    self.cas_host(
    #        rv, 'INT',
    #        remote = self.remote,
    #        interaction = 'internal',
    #    )

    #    def cb(value):
    #        print("RV_INT({0}): ".format(self.name), value)

    #    rv.register(callback = cb)
    #    return rv

    #@declarative.dproperty
    #def rv_str(self):
    #    rv = cas9epics.RelayValueString("test")
    #    self.cas_host(
    #        rv, 'STR',
    #        remote = self.remote,
    #        interaction = 'internal',
    #    )

    #    def cb(value):
    #        print("RV_STR({0}): ".format(self.name), value)

    #    rv.register(callback = cb)
    #    return rv


class Testers(cas9epics.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVConnects(
            name = 'connects',
            subprefix = None,
            parent = self,
        )

if __name__ == "__main__":
    Testers.cmdline(
        module_name_base = 'RVInternal',
    )

