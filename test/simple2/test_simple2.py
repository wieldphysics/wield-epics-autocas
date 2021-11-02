"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
from wavestate.epics import autocas


class RVTester(cas9epics.CASUser):
    @cas9epics.dproperty
    def rv_test(self):
        rv = cas9epics.RelayValueFloat(0)
        self.cas_host(
            rv,
            "VAL",
            unit="seconds",
            interaction="setting",
            prec=4,
            lolo=-1,
            low=0,
            high=10,
            hihi=100,
            lolim=1,
            hilim=self.rv_test_hi,
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback=cb)
        return rv

    @cas9epics.dproperty
    def rv_test_hi(self):
        return cas9epics.RelayValueFloat(10)

    task_period_s = 1 / 8.0

    @cas9epics.dproperty
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


if __name__ == "__main__":
    root = cas9epics.InstaCAS()
    test = RVTester(
        name="TEST",
        parent=root,
    )

    test2 = RVTester(
        name="TEST2",
        parent=root,
        task_period_s=1,
    )

    test.rv_test.value = 10
    test.rv_test_hi.value = 100
    test2.rv_test_hi.value = 25
    root.run()
