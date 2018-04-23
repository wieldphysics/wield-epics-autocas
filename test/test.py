"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
from YALL.controls.instacas import reactor
from YALL.controls.instacas import cas
import pcaspy
import pcaspy.tools

from YALL.controls.instacas.relay_values import (
    RelayValueFloat, RelayValueCoerced, RelayValueRejected
)

rv_test = RelayValueFloat(0)
rv_test_hi = RelayValueFloat(10)

db = {
    'X1:TEST-VAL': {
        'type':      'float',
        'unit':      'seconds',
        'prec':      4,
        'lolo':     -1,
        'low':      0,
        'high':     10,
        'hihi':     100,
        'lolim':     1,
        'hilim':     rv_test_hi,
        'rv' :       rv_test,
        'writable' : True,
    },
}

def cb(value):
    print("RV_TEST: ", value)

rv_test.register(callback = cb)

if __name__ == "__main__":
    react = reactor.Reactor()

    with cas.CADriverServer(db, react):
        rv_test.value = 10
        rv_test_hi.value = 100
        react.run_reactor()
