#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
from declarative import (
    contexts.ParentCarrier,
    declarative.dproperty, declarative.NOARG,
    #declarative.mproperty,
)

from YALL.controls.epics import EpicsCarrier

from YALL.controls.epics.panels import (
    epics_panels.VHNestedMEDM,
)

from .components.service import PicomotorConnectionService
from .components.reactor import PicomotorRelay


class PicomotorGroupController(epics.EpicsCarrier, contexts.ParentCarrier):

    @declarative.dproperty
    def picomotor_address(self, tcp_addr = declarative.NOARG):
        if tcp_addr is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return tcp_addr

    @declarative.dproperty
    def ebridge(self, ebridge = declarative.NOARG):
        if ebridge is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return ebridge

    @declarative.dproperty
    def picomotor_connection_service(self):
        sys = PicomotorConnectionService(
            ebridge_service    = self.ebridge.connection_service,
            ebridge_connection = self.ebridge.connection,
            socket_address     = self.picomotor_address,
            egroup             = self.egroup.child("PCS"),
            parent             = self,
        )
        return sys

    @declarative.dproperty
    def prm(self):
        PicomotorRelay(
            ebridge = self.ebridge.prm,
            reactor = self.picomotor_connection_service.reactor,
            device_num_x  = 1,
            motor_num_x   = 2,
            device_num_y  = 2,
            motor_num_y   = 0,
        )
        return None

    @declarative.dproperty
    def beamsplitter(self):
        PicomotorRelay(
            ebridge = self.ebridge.beamsplitter,
            reactor = self.picomotor_connection_service.reactor,
            device_num_x  = 1,
            motor_num_x   = 0,
            device_num_y  = 1,
            motor_num_y   = 1,
        )
        return None

    @declarative.dproperty
    def injection(self):
        PicomotorRelay(
            ebridge = self.ebridge.injection,
            reactor = self.picomotor_connection_service.reactor,
            device_num_x  = 2,
            motor_num_x   = 1,
            device_num_y  = 2,
            motor_num_y   = 2,
        )
        return None

    @declarative.dproperty
    def telescope_near(self):
        PicomotorRelay(
            ebridge = self.ebridge.telescope_near,
            reactor = self.picomotor_connection_service.reactor,
            device_num_x  = 3,
            motor_num_x   = 0,
            device_num_y  = 3,
            motor_num_y   = 1,
        )
        return None

    @declarative.dproperty
    def telescope_far(self):
        PicomotorRelay(
            ebridge = self.ebridge.telescope_far,
            reactor = self.picomotor_connection_service.reactor,
            device_num_x  = 3,
            motor_num_x   = 2,
            device_num_y  = 4,
            motor_num_y   = 0,
        )
        return None

    @declarative.dproperty
    def medm_panel_status(self):
        medm = epics_panels.VHNestedMEDM(
            [
                self.picomotor_connection_service.medm_panel,
            ],
        )
        medm.medm_screen_filename_from_namechain(self.ebridge.egroup.name_chain.child('STATUS'))
        return medm

    def medm_tree(self):
        return (
            self.ebridge.medm_panel_1,
            self.ebridge.medm_panel_2,
        )


