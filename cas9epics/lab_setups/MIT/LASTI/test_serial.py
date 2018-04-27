"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

import cas9epics
from cas9epics import serial
from cas9epics.devices.IFR2023 import IFR2023


class IFR2023Controller(cas9epics.CAS9Module):
    @cas9epics.dproperty
    def gpib(self):
        return serial.USBPrologixGPIB(
            name = 'GPIB',
            parent = self,
            _debug_echo = True,
        )

    @cas9epics.dproperty
    def gpibLOELF(self):
        return self.gpib.address_gpib_create(
            GPIB_addr = '0',
            parent = self,
            name = 'GPIB_LOELF'
        )

    @cas9epics.dproperty
    def siggen2023(self):
        return IFR2023(
            serial = self.gpibLOELF,
            name   = 'sg2023',
            parent = self,
        )

    @cas9epics.dproperty
    def cmd2023(self):
        return serial.SerialCommandResponse(
            serial = self.gpibLOELF,
            name   = 'cmd2023',
            parent = self,
        )


if __name__ == "__main__":
    IFR2023Controller.cmdline(
        module_name_base = 'LOELF',
    )
