"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""

import sys
from wield.epics import autocas
from wield import declarative


class RVExternals(autocas.CASUser):
    @declarative.dproperty
    def rv_internal(self):
        rv = autocas.RelayValueFloat(0)
        self.cas_host(
            rv,
            "INT",
            remote=False,
            urgentsave_s=0.1,
            interaction="internal",
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @declarative.dproperty
    def rv_test(self):
        rv = autocas.RelayValueFloat(0)
        self.cas_host(
            rv,
            "EXT",
            prefix=["ISC", "ADC28", "GAIN"],
            remote=True,
            interaction="internal",
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv


class Testers(autocas.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVExternals(
            name="TEST",
            parent=self,
        )


if __name__ == "__main__":
    Testers.cmdline(
        module_name_base="RVExternal",
    )
