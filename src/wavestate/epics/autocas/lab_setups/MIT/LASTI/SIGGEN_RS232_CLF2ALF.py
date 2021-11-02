"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""


import cas9epics
from cas9epics import serial
from cas9epics.devices.IFR2026 import IFR2026


class IFR2026Controller(cas9epics.CAS9Module):
    @cas9epics.dproperty
    def serial(self):
        return serial.USBDeviceRS232(
            name="SERIAL",
            parent=self,
            _debug_echo=True,
        )

    @cas9epics.dproperty
    def CLF2ALF(self):
        return IFR2026(
            serial=self.serial,
            name="CLF2ALF",
            parent=self,
        )

    @cas9epics.dproperty
    def CLF2ALF_CMD(self):
        return serial.SerialCommandResponse(
            serial=self.serial,
            name="CLF2ALF_CMD",
            parent=self,
        )


if __name__ == "__main__":
    IFR2026Controller.cmdline(
        module_name_base="CLF2ALF",
    )
