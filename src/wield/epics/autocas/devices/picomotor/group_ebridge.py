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
    declarative.OverridableObject,
    declarative.dproperty, declarative.NOARG,
    contexts.ParentCarrier,
    #declarative.mproperty,
)
from YALL.controls.epics import EpicsCarrier

from .components.mappings import (
    PicomotorConnectionMapping,
    PicomotorMapping,
    PicomotorSingleMapping
)

from .components.service import (
    PicomotorConnectionEBridge,
)

from YALL.controls.epics.panels import (
    epics_panels.HVNestedMEDM,
    #epics_panels.VHNestedMEDM,
    #LinkButtonMEDM,
)


class PicomotorGroupEBridge(
    contexts.ParentCarrier,
    epics.EpicsCarrier,
    declarative.OverridableObject,
):

    @declarative.dproperty
    def connection_service(self):
        ebrg = PicomotorConnectionEBridge(
            egroup     = self.egroup,
        )
        return ebrg

    @declarative.dproperty
    def connection(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = PicomotorConnectionMapping(
                egroup     = self.egroup.child("connection"),
            )
        return ebrg

    @declarative.dproperty
    def prm(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = PicomotorMapping(
                display_name = "Power Recycle Mirror",
                connect_epics = self.connection,
                egroup        = self.egroup.child("PRM"),
            )
        return ebrg

    @declarative.dproperty
    def beamsplitter(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = PicomotorMapping(
                display_name = "Beam Splitter",
                connect_epics = self.connection,
                egroup        = self.egroup.child("BS"),
            )
        return ebrg

    @declarative.dproperty
    def injection(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = PicomotorMapping(
                display_name  = "Injection Periscope",
                connect_epics = self.connection,
                egroup        = self.egroup.child("inject"),
            )
        return ebrg

    @declarative.dproperty
    def telescope_near(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = PicomotorMapping(
                display_name = "Telescope Near",
                connect_epics = self.connection,
                egroup        = self.egroup.child("TLSN"),
            )
        return ebrg

    @declarative.dproperty
    def telescope_far(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            ebrg = PicomotorMapping(
                display_name = "Telescope Far",
                connect_epics = self.connection,
                egroup        = self.egroup.child("TLSF"),
            )
        return ebrg

    @declarative.dproperty
    def medm_panel_1(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            panel = epics_panels.HVNestedMEDM(
                [
                    self.injection.medm_panel,
                    self.prm.medm_panel,
                    self.beamsplitter.medm_panel,
                ],
            )
        panel.medm_screen_filename_from_namechain(self.egroup.name_chain.child('pico1'))
        return panel

    @declarative.dproperty
    def medm_panel_2(self, ebrg = declarative.NOARG):
        if ebrg is declarative.NOARG:
            panel = epics_panels.HVNestedMEDM(
                [
                    self.telescope_near.medm_panel,
                    self.telescope_far.medm_panel,
                ]
            )
        panel.medm_screen_filename_from_namechain(self.egroup.name_chain.child('pico2'))
        return panel


