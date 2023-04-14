#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import os.path as path

from declarative import (
    declarative.dproperty, declarative.NOARG,
    declarative.RelayBool, declarative.RelayBoolAll,
)

from YALL.controls.epics import (
    epics.EpicsCarrier,
    epics.MEDMScreenHolder,
    MEDMTemplatePanel
)

from YALL.libholo.contexts import (
    contexts.ToplevelActive,
    EpicsConnectable
)

from YALL.libholo.tools import (
    declarative.RelayBoolEpics,
)

from .reactor import PicomotorBridgeReactor


class PicomotorConnectionEBridge(epics.EpicsCarrier):
    pass


class PicomotorConnectionService(epics.EpicsCarrier, contexts.ToplevelActive, contexts.EpicsConnectable):

    @declarative.dproperty
    def ebridge_service(self, ebridge = declarative.NOARG):
        if ebridge is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return ebridge

    @declarative.dproperty
    def ebridge_connection(self, ebridge = declarative.NOARG):
        if ebridge is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return ebridge

    @declarative.dproperty
    def socket_address(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return val

    @declarative.dproperty
    def state_fake(self, rbool = declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBool(False)
        return rbool

    @declarative.dproperty
    def rbool_epics(self, ebool = declarative.NOARG):
        if ebool is declarative.NOARG:
            ebool = declarative.RelayBoolEpics(
                egroup = self.egroup.child('BE'),
                parent = self,
            )
        return ebool

    @declarative.dproperty
    def postfix(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            val = None
        return val

    @declarative.dproperty
    def display_name(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            val = 'Picomotor Telnet'
            if self.postfix is not None:
                val = val + " For " + self.postfix
        return val

    @declarative.dproperty
    def state_active(self, rbool = declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBoolAll()
        rbool.bool_register(self.state_active_toplevel)
        rbool.bool_register(self.state_enable)
        return rbool

    @declarative.dproperty
    def state_enable(self):
        rbool = declarative.RelayBool(False)
        self.rbool_epics.bool_view_set("ENABLE", rbool, settable = True)
        self.rbool_epics.bool_button_set("ENABLE", rbool)
        return rbool

    @declarative.dproperty
    def state_connected(self, rbool = declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBool(False)
        self.rbool_epics.bool_view_set("CONNECTED", rbool)
        return rbool

    @declarative.dproperty
    def medm_panel(self):
        return PicomotorConnectionPanel(system = self)

    @declarative.dproperty
    def reactor(self):
        rct = PicomotorBridgeReactor(
            socket_address = self.socket_address,
            ebridge = self.ebridge_connection,
            state_fake = self.state_fake,
            state_active = self.state_active,
            state_connected = self.state_connected,
        )
        return rct


class PicomotorConnectionPanel(epics.MEDMScreenHolder):
    """
    """

    @declarative.dproperty
    def system(self, sys = declarative.NOARG):
        if sys is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return sys

    def generate_medm(self):
        MEDM_FNAME = path.join(path.dirname(__file__), 'medm', 'CONNECTION_SERVICE.adl')

        pvs_by_part = {}
        extra_replace = dict(
            TITLE = self.system.display_name
        )
        #pvs_by_part.update(self.system.PVs_by_part)
        self.system.rbool_epics.augment_medm(pvs_by_part, extra_replace)

        panel = epics.MEDMTemplatePanel(
            MEDM_FNAME,
            pvs_by_part,
            embed_panels = self.embed_panels(),
            extra_replace = extra_replace,
        )
        return panel


