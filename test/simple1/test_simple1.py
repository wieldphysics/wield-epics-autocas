"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import cas9epics

rv_test = cas9epics.RelayValueFloat(0)
rv_test_hi = cas9epics.RelayValueFloat(10)

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
    reactor = cas9epics.Reactor()

    with cas9epics.CADriverServer(db, reactor):
        rv_test.value = 10
        rv_test_hi.value = 100
        while True:
            reactor.flush(modulo_s = 1/8.)

            if rv_test.value >= 100:
                rv_test.value = 0
                rv_test_hi.value += 1
            else:
                rv_test.value += 1
