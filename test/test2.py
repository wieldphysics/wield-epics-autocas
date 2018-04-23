"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
from YALL.controls.instacas import reactor
from YALL.controls.instacas import cas
from YALL.controls.instacas import instacas
import declarative

from YALL.controls.instacas.relay_values import (
    RelayValueFloat, RelayValueCoerced, RelayValueRejected
)


class RVTester(instacas.CASUser):
    @declarative.dproperty
    def rv_test(self):
        rv = RelayValueFloat(0)
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
            print("RV_TEST: ", value)
        rv.register(callback = cb)
        return rv

    @declarative.dproperty
    def rv_test_hi(self):
        return RelayValueFloat(10)


if __name__ == "__main__":
    root = instacas.InstaCAS()
    test = RVTester(
        name = 'TEST',
        parent = root,
    )

    print(root.rv_names)
    print(root.rv_db)
    print(root.cas_db_generate())

    test.rv_test.value = 10
    test.rv_test_hi.value = 100
    root.run()
