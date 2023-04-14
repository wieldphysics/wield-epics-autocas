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

import YALL.controls.core.contexts as contexts
import YALL.controls.epics as epics


class FiberMonEBridge(
    # contexts.EpicsCarrier,
    epics.EpicsRelayUser,
    contexts.ParentCarrier,
    epics.Connectable,
):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    name = "<NONAME>"

    @declarative.dproperty
    def inmon(self, ebr):
        return ebr

    @declarative.dproperty
    def outP(self, ebr):
        return ebr

    @declarative.dproperty
    def outS(self, ebr):
        return ebr

    @RELAY_EPICS.float_value_add("OUTT", precision=2, value=0, binding_type="ext")
    @declarative.dproperty
    def rv_out_total(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("OUTTPERC", precision=2, value=0, binding_type="ext")
    @declarative.dproperty
    def rv_out_total_percent(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("OUTTPERC_BEST", precision=2, value=0)
    @declarative.dproperty
    def rv_out_total_percent_best(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add(
        "OUTP_PERCTOT", precision=2, value=0, binding_type="ext"
    )
    @declarative.dproperty
    def rv_outP_percent_total(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add(
        "OUTS_PERCTOT", precision=2, value=0, binding_type="ext"
    )
    @declarative.dproperty
    def rv_outS_percent_total(self):
        rv = declarative.RelayValue(0)
        return rv

    @declarative.mproperty
    def medm_panel(self):
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="FIBERS.adl",
        )
        medm.medm_screen_filename_from_namechain(self.egroup.name_chain.child("FIBERS"))
        return medm

    def medm_embed_panels(self):
        return {
            "OUTP": self.outP.medm_view_panel,
            "OUTS": self.outS.medm_view_panel,
            "INMON": self.inmon.medm_view_panel,
        }

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(FiberMonEBridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        self.inmon.augment_medm(pvs_by_part, extra_replace, prefix=prefix + "INMON_")
        self.outP.augment_medm(pvs_by_part, extra_replace, prefix=prefix + "OUTP_")
        self.outS.augment_medm(pvs_by_part, extra_replace, prefix=prefix + "OUTS_")
        extra_replace["TITLE"] = self.name
        # extra_replace['PANEL_FNAME'] = self.medm_settings_panel.medm_screen_filename
        return


class FiberMonController(
    contexts.AlertsUser,
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject,
):
    master_mode = True

    @declarative.dproperty
    def ebridge(self, ebr):
        ebr.rv_connect_mode.value = "master"
        ebr.state_connect.bool_register(self.state_connect_epics)
        return ebr

    @declarative.dproperty
    def dividers_setup(self):
        def div_all(value=None):
            self.ebridge.rv_out_total.value = (
                self.ebridge.outS.rv_mw.value + self.ebridge.outP.rv_mw.value
            )
            try:
                self.ebridge.rv_out_total_percent.value = (
                    100
                    * self.ebridge.rv_out_total.value
                    / self.ebridge.inmon.rv_mw.value
                )
            except ZeroDivisionError:
                self.ebridge.rv_out_total_percent.value = -8888.8888
                pass
            try:
                self.ebridge.rv_outP_percent_total.value = 100 * (
                    self.ebridge.outP.rv_mw.value / self.ebridge.rv_out_total.value
                )
            except ZeroDivisionError:
                self.ebridge.rv_outP_percent_total.value = -8888.8888
                pass
            try:
                self.ebridge.rv_outS_percent_total.value = 100 * (
                    self.ebridge.outS.rv_mw.value / self.ebridge.rv_out_total.value
                )
            except ZeroDivisionError:
                self.ebridge.rv_outS_percent_total.value = -8888.8888
                pass

        self.ebridge.inmon.rv_mw.register(
            callback=div_all,
        )

        self.ebridge.outP.rv_mw.register(
            callback=div_all,
        )

        self.ebridge.outS.rv_mw.register(
            callback=div_all,
        )

        # so that we can access all of the methods for potential removal
        return Bunch(locals())
