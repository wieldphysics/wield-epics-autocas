"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

import cas9epics
from cas9epics import serial


class IFR2026Controller(cas9epics.CAS9Module):
    def serial(val):
        return serial.SerialConnection(
            name = 'SERIAL',
            parent = self,
        )

    def siggen2026(val):
        return serial.SerialConnection(
            serial = self.serial,
            name   = 'sg2026',
            parent = self,
        )

if __name__ == "__main__":
    root = instacas.InstaCAS()
    print(myserial.prefix_full)
    print(my2026.chnB.prefix_full)

    #print(root.rv_names)
    #print(root.rv_db)
    #print(root.cas_db_generate())
    for pv_name, db in root.cas_db_generate().items():
        print("PV: ", pv_name)
    root.run()
