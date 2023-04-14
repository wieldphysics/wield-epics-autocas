"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""

import sys
from wield.epics import autocas
from wield import declarative


class RVConnects(autocas.CASUser):
    remote = False

    @declarative.dproperty
    def rv_fl(self):
        rv = autocas.RelayValueFloat(0)
        self.cas_host(
            rv,
            "FL",
            remote=self.remote,
            interaction="internal",
        )

        def cb(value):
            print("RV_FL({0}): ".format(self.name), value)

        rv.register(callback=cb, key=self)

        if not self.remote:

            def update():
                rv.value += 0.1

            self.reactor.enqueue_looping(update, period_s=0.1)
        return rv

    # @declarative.dproperty
    # def rv_int(self):
    #    rv = autocas.RelayValueInt(0)
    #    self.cas_host(
    #        rv, 'INT',
    #        remote = self.remote,
    #        interaction = 'internal',
    #    )

    #    def cb(value):
    #        print("RV_INT({0}): ".format(self.name), value)

    #    rv.register(callback = cb)
    #    return rv

    # @declarative.dproperty
    # def rv_str(self):
    #    rv = autocas.RelayValueString("test")
    #    self.cas_host(
    #        rv, 'STR',
    #        remote = self.remote,
    #        interaction = 'internal',
    #    )

    #    def cb(value):
    #        print("RV_STR({0}): ".format(self.name), value)

    #    rv.register(callback = cb)
    #    return rv


class Testers(autocas.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVConnects(
            name="connects",
            subprefix=None,
            parent=self,
        )


if __name__ == "__main__":
    Testers.cmdline(
        module_name_base="RVInternal",
    )
