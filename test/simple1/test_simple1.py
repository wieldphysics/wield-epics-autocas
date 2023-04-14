"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""

from wield.epics import autocas

rv_test = autocas.RelayValueFloat(0)
rv_test_hi = autocas.RelayValueFloat(10)

db = {
    "X1:TEST-VAL": {
        "type": "float",
        "unit": "seconds",
        "prec": 4,
        "lolo": -1,
        "low": 0,
        "high": 10,
        "hihi": 100,
        "lolim": 1,
        "hilim": rv_test_hi,
        "rv": rv_test,
        "interaction": "internal",
    },
}


def cb(value):
    print("RV_TEST: ", value)


rv_test.register(callback=cb)

if __name__ == "__main__":
    reactor = autocas.Reactor()

    with autocas.CADriverServer(db, reactor):
        rv_test.value = 10
        rv_test_hi.value = 100
        while True:
            reactor.flush(modulo_s=1 / 8.0)

            if rv_test.value >= 100:
                rv_test.value = 0
                rv_test_hi.value += 1
            else:
                rv_test.value += 1
