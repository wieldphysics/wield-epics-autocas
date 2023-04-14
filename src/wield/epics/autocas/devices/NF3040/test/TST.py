#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


from wield import declarative

from YALL.controls.core import (
    StandardSystem,
    StandardSystemEBridge,
    AlertSystem,
)

from YALL.controls.core.meta_system import (
    MetaSystemMedm,
    MetaSystemEBridge,
)

from YALL.controls import epics
from YALL.controls.epics import panels as epics_panels

from YALL.controls.peripherals.NF3040.service import NF3040Runner, NF3040Ebridge


class EBridge(
    StandardSystemEBridge,
    epics.Connectable,
):
    system_name = "TST"

    @declarative.mproperty
    def meta(self, ebr=declarative.NOARG):
        if ebr is declarative.NOARG:
            ebr = MetaEBridge(
                local=self.local,
                ifo=self.ifo,
            )
        return ebr

    @declarative.dproperty
    def NF3040(self):
        ebr = NF3040Ebridge(
            parent=self,
            egroup=self.egroup.child("3040"),
            display_name="SHG Temp Controller",
        )
        return ebr


class System(
    StandardSystem,
    declarative.OverridableObject,
):
    @declarative.dproperty
    def ebridge(self):
        return EBridge(
            ifo=self.ifo,
            local=self.local,
        )

    @declarative.dproperty
    def alerts(self, alerts=declarative.NOARG):
        alerts = AlertSystem(prefix="SHG")
        return alerts

    @declarative.dproperty
    def NF3040(self):
        return NF3040Runner(
            parent=self,
            ebridge=self.ebridge.NF3040,
        )

    @declarative.mproperty
    def medm_overview(self):
        button = epics_panels.button_factory(which="medium_bright")
        panel = epics_panels.VHNestedMEDM(
            [
                button("3040", self.NF3040.medm_full_panel),
            ],
        )
        return panel


class MetaEBridge(MetaSystemEBridge):
    message_sequence_len = 20
    script_title = "NF3040 Test"
    host_ifo_map = {
        "M1": "lambda.local",
    }
    system_name = "TST"

    @declarative.dproperty
    def medm_master_adl(self):
        val = "{0}_MASTER_TST.adl".format(self.ifo)
        return val


class Meta(MetaSystemMedm):
    system_name = "TST"
    script_title = "TST System"
    t_system = System
    t_ebridge = MetaEBridge
