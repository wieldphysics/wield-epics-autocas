"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
import sys
from wield.epics import autocas
from wield import declarative
from wield.epics.autocas.utilities import pprint
from wield.epics.autocas.subservices.restart_on_edit import RestartOnEdit


class RVTester(autocas.CASUser):
    @declarative.dproperty
    def rv_test(self):
        rv = autocas.RelayValueFloat(0)
        self.cas_host(
            rv,
            "VAL",
            unit="seconds",
            interaction="internal",
            prec=4,
            lolo=-1,
            low=0,
            high=10,
            hihi=100,
            lolim=1,
            hilim=self.rv_test_hi,
            urgentsave_s=0.1,
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @declarative.dproperty
    def rv_test_hi(self):
        return autocas.RelayValueFloat(10)

    task_period_s = 1 / 8.0

    @declarative.dproperty
    def my_action(self):
        def task():
            if self.rv_test.value >= 100:
                self.rv_test.value = 0
                self.rv_test_hi.value += 1
            else:
                self.rv_test.value += 1

        self.reactor.enqueue_looping(task, period_s=self.task_period_s)
        # return the task in case we want to tell the reactor to stop later
        return task


class Testers(autocas.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVTester(
            name="TEST",
            parent=self,
        )

    @declarative.dproperty
    def test2(self):
        return RVTester(
            name="TEST2",
            parent=self,
            task_period_s=1,
        )


if __name__ == "__main__":
    Testers.cmdline(
        module_name_base="RVbasic",
    )
