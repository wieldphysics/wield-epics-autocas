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

from YALL.controls.core import contexts
from YALL.controls import epics
from YALL.controls.epics import panels as epics_panels

from .components.service import (
    SR560SerialService,
    SR560Relay,
)


class SR560GroupController(epics.EpicsCarrier, contexts.ParentCarrier):
    @declarative.dproperty
    def ebridge(self, ebridge=declarative.NOARG):
        if ebridge is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return ebridge

    @declarative.dproperty
    def serial_service(self):
        sys = SR560SerialService(
            ebridge_service=self.ebridge.connection_service,
            egroup=self.egroup.child("SS"),
            parent=self,
        )
        return sys

    @declarative.dproperty
    def carm(self):
        SR560Relay(
            serial_service=self.serial_service,
            ebridge=self.ebridge.carm,
            # display_name   = self.ebridge.carm.display_name,
            # repics_ebridge = self.ebridge.carm.repics_ebridge,
            # egroup         = self.ebridge.carm.egroup,
            parent=self,
        )
        return None

    @declarative.dproperty
    def medm_panel_status(self):
        medm = epics_panels.VHNestedMEDM(
            [
                self.serial_service.medm_panel,
            ],
        )
        medm.medm_screen_filename_from_namechain(
            self.ebridge.egroup.name_chain.child("STATUS")
        )
        return medm

    def medm_tree(self):
        return (self.ebridge.medm_panel_1,)
