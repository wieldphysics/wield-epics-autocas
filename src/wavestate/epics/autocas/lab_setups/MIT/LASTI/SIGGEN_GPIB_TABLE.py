"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""


import cas9epics
from cas9epics import serial
from cas9epics.devices.IFR2023 import IFR2023

# from cas9epics.devices.IFR2026 import IFR2026
from cas9epics.devices.SRS_SG380 import SRS_SG380


class IFR2023Controller(cas9epics.CAS9Module):
    @cas9epics.dproperty
    def gpib(self):
        return serial.USBPrologixGPIB(
            name="GPIB",
            parent=self,
            _debug_echo=True,
        )

    @cas9epics.dproperty
    def gpibLOELF(self):
        return self.gpib.address_gpib_create(
            GPIB_addr="0",
            parent=self,
            name="GPIB_LOELF",
        )

    @cas9epics.dproperty
    def siggen2023(self):
        return IFR2023(
            serial=self.gpibLOELF,
            name="LOELF",
            parent=self,
        )

    @cas9epics.dproperty
    def cmd2023(self):
        return serial.SerialCommandResponse(
            serial=self.gpibLOELF,
            name="LOELF_CMD",
            parent=self,
        )

    ##Not functioning well over GPIB, so running separately over RS232
    # @cas9epics.dproperty
    # def gpibCLF2ALF(self):
    #    return self.gpib.address_gpib_create(
    #        GPIB_addr = '30',
    #        parent = self,
    #        name = 'GPIB_CLF2ALF',
    #    )
    #
    # @cas9epics.dproperty
    # def CLF2ALF_IFR2026(self):
    #    return IFR2026(
    #        serial = self.gpibCLF2ALF,
    #        name   = 'CLF2ALF',
    #        parent = self,
    #    )

    # @cas9epics.dproperty
    # def CLF2ALF_cmd(self):
    #    return serial.SerialCommandResponse(
    #        serial = self.gpibCLF2ALF,
    #        name   = 'CLF2ALF_CMD',
    #        parent = self,
    #    )

    @cas9epics.dproperty
    def gpibFCG(self):
        return self.gpib.address_gpib_create(
            GPIB_addr="3",
            parent=self,
            name="GPIB_FCG",
        )

    @cas9epics.dproperty
    def FCG_SG382(self):
        return SRS_SG380(
            serial=self.gpibFCG,
            name="FCG",
            parent=self,
        )

    @cas9epics.dproperty
    def FCG_cmd(self):
        return serial.SerialCommandResponse(
            serial=self.gpibFCG,
            name="FCG_CMD",
            parent=self,
        )

    @cas9epics.dproperty
    def gpibCLF1(self):
        return self.gpib.address_gpib_create(
            GPIB_addr="2",
            parent=self,
            name="GPIB_CLF1",
        )

    @cas9epics.dproperty
    def CLF1_SG382(self):
        return SRS_SG380(
            serial=self.gpibCLF1,
            name="CLF1",
            parent=self,
        )

    @cas9epics.dproperty
    def CLF1_cmd(self):
        return serial.SerialCommandResponse(
            serial=self.gpibCLF1,
            name="CLF1_CMD",
            parent=self,
        )


if __name__ == "__main__":
    IFR2023Controller.cmdline(
        module_name_base="LOELF",
    )
