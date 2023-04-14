"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
import sys
from wield.epics import autocas

# from wield.epics.autocas.utilities import pprint


class RVTester(autocas.CASUser):
    @autocas.dproperty
    def rv_test_float(self):
        rv = autocas.RelayValueFloat(0)
        self.cas_host(
            rv,
            "VAL",
            unit="seconds",
            interaction="setting",
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST_FLOAT({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @autocas.dproperty
    def rv_test_str(self):
        rv = autocas.RelayValueString("hello")
        self.cas_host(
            rv,
            "STR",
            interaction="setting",
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST_STRING({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @autocas.dproperty
    def rv_test_long_str(self):
        rv = autocas.RelayValueLongString("hello")
        self.cas_host(
            rv,
            "STRL",
            interaction="setting",
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST_LSTRING({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @autocas.dproperty
    def rv_test_bool(self):
        rv = autocas.RelayBool(False)
        self.cas_host(
            rv,
            "BOOL",
            interaction="setting",
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST_BOOL({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @autocas.dproperty
    def rv_test_enum(self):
        rv = autocas.RelayValueEnum("A", ["A", "B", "C"])
        self.cas_host(
            rv,
            "ENUM",
            interaction="setting",
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST_ENUM({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv


class Testers(autocas.CAS9Module):
    @autocas.dproperty
    def save(self):
        return RVTester(
            name="SAVE",
            parent=self,
        )


if __name__ == "__main__":
    Testers.cmdline(
        module_name_base="RVtypes",
    )
