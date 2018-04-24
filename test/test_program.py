"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import sys
import cas9epics
import declarative
from cas9epics.utilities import pprint
from cas9epics.subservices.restart_on_edit import RestartOnEdit


class RVTester(cas9epics.CASUser):
    @declarative.dproperty
    def rv_test(self):
        rv = cas9epics.RelayValueFloat(0)
        self.cas_host(
            rv, 'VAL',
            unit  = 'seconds',
            writable = True,
            prec  = 4,
            lolo  = -1,
            low   = 0,
            high  = 10,
            hihi  = 100,
            lolim = 1,
            hilim = self.rv_test_hi,
        )

        def cb(value):
            print("RV_TEST({0}): ".format(self.name), value)

        rv.register(callback = cb)
        return rv

    @declarative.dproperty
    def rv_test_hi(self):
        return cas9epics.RelayValueFloat(10)

    task_period_s = 1/8.

    @declarative.dproperty
    def my_action(self):
        def task():
            if self.rv_test.value >= 100:
                self.rv_test.value = 0
                self.rv_test_hi.value += 1
            else:
                self.rv_test.value += 1
        self.reactor.enqueue_looping(task, period_s = self.task_period_s)
        #return the task in case we want to tell the reactor to stop later
        return task


class Testers(cas9epics.CASUser):
    @declarative.dproperty
    def test(self):
        return RVTester(
            name = 'TEST',
            parent = self,
        )

    @declarative.dproperty
    def test2(self):
        return RVTester(
            name = 'TEST2',
            parent = self,
            task_period_s = 1,
        )

class Program(cas9epics.CAS9CmdLine):
    t_task = Testers


if __name__ == "__main__":
    Program.__cls_argparse__()

