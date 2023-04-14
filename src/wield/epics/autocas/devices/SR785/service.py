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
from YALL.controls import epics
from YALL.controls.epics import panels as epics_panels
from YALL.controls.core import contexts


retdata_len = 1000


class SR785Ebridge(epics.EpicsRelayUser):
    """ """

    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @declarative.dproperty
    def display_name(self, name=declarative.NOARG):
        if name is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return name

    @declarative.mproperty
    def medm_panel(self):
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="SR785.adl",
        )
        medm.medm_screen_filename_from_namechain(self.egroup.name_chain.child("PANEL"))
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(SR785Ebridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["TITLE"] = self.display_name
        return

    @RELAY_EPICS.float_value_add("TRIG", precision=3)
    @declarative.dproperty
    def rv_trig(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.array_value_add("FREQ", precision=3, length=retdata_len)
    @declarative.dproperty
    def rv_freq_Hz(self):
        rv = declarative.RelayValue([0])
        return rv

    @RELAY_EPICS.array_value_add("MAG", precision=3, length=retdata_len)
    @declarative.dproperty
    def rv_magnitude(self):
        rv = declarative.RelayValue([0])
        return rv

    @RELAY_EPICS.array_value_add("MAG_UP", precision=3, length=retdata_len)
    @declarative.dproperty
    def rv_magnitude_up(self):
        rv = declarative.RelayValue([0])
        return rv

    @RELAY_EPICS.array_value_add("MAG_DN", precision=3, length=retdata_len)
    @declarative.dproperty
    def rv_magnitude_dn(self):
        rv = declarative.RelayValue([0])
        return rv

    @RELAY_EPICS.array_value_add("PHASE", precision=3, length=retdata_len)
    @declarative.dproperty
    def rv_phase_deg(self):
        rv = declarative.RelayValue([0])
        return rv

    @RELAY_EPICS.array_value_add("SNR", precision=3, length=retdata_len)
    @declarative.dproperty
    def rv_SNR(self):
        rv = declarative.RelayValue([0])
        return rv


class SR785Runner(
    contexts.AlertsUser,
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject,
):
    @declarative.dproperty
    def ebridge(self, ebr):
        return ebr
