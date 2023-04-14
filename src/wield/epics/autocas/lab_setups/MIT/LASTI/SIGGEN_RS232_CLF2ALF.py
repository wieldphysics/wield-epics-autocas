#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""


from wield.epics import autocas
from wield.epics.autocas import serial
from wield.epics.autocas.devices.IFR2026 import IFR2026


class IFR2026Controller(autocas.CAS9Module):
    @autocas.dproperty
    def serial(self):
        return serial.USBDeviceRS232(
            name="SERIAL",
            parent=self,
            _debug_echo=True,
        )

    @autocas.dproperty
    def CLF2ALF(self):
        return IFR2026(
            serial=self.serial,
            name="CLF2ALF",
            parent=self,
        )

    @autocas.dproperty
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
