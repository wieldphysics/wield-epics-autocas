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
from wield.epics.autocas.devices.TEK_AFG3000 import TEK_AFG3000


class IFR2023Controller(autocas.CAS9Module):
    @autocas.dproperty
    def serial(self):
        return serial.VXI11Connection(
            name="VXI11",
            parent=self,
            _debug_echo=True,
            timeout_s=1,
        )

    @autocas.dproperty
    def CLFDEMOD(self):
        return TEK_AFG3000(
            serial=self.serial,
            name="CLFDEMOD",
            parent=self,
        )

    @autocas.dproperty
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
