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

from YALL.controls.instacas import serial


if __name__ == "__main__":
    root = instacas.InstaCAS()
    myserial = serial.SerialConnection(
        name = 'SERIAL',
        parent = root,
    )
    my2026 = serial.IFR2026Controls(
        name = '2026',
        parent = root,
        serial = myserial,
    )
    print(myserial.prefix_full)
    print(my2026.chnB.prefix_full)

    #print(root.rv_names)
    #print(root.rv_db)
    #print(root.cas_db_generate())
    for pv_name, db in root.cas_db_generate().items():
        print("PV: ", pv_name)
    root.run()
