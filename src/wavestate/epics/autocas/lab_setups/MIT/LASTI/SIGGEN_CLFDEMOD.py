"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

import cas9epics
from cas9epics import serial
from cas9epics.devices.TEK_AFG3000 import TEK_AFG3000


class IFR2023Controller(cas9epics.CAS9Module):
    @cas9epics.dproperty
    def serial(self):
        return serial.VXI11Connection(
            name="VXI11",
            parent=self,
            _debug_echo=True,
            timeout_s=1,
        )

    @cas9epics.dproperty
    def CLFDEMOD(self):
        return TEK_AFG3000(
            serial=self.serial,
            name="CLFDEMOD",
            parent=self,
        )

    @cas9epics.dproperty
    def cmd2023(self):
        return serial.SerialCommandResponse(
            serial=self.serial,
            name="CLFDEMOD_CMD",
            parent=self,
        )


if __name__ == "__main__":
    IFR2023Controller.cmdline(
        module_name_base="LOELF",
    )
