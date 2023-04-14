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


class SR560Ebridge(epics.EpicsRelayUser):
    """ """

    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))
    master_mode = False

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
            medm_template="SR560.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(SR560Ebridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["TITLE"] = self.display_name
        return

    @RELAY_EPICS.bool_add("AUTOLOAD", buttons=True, binding_type="RW")
    @declarative.dproperty
    def state_autoload(self):
        rbool = declarative.RelayBool(False)
        return rbool

    @RELAY_EPICS.callback_add("CLEAR_OVERLOAD")
    @declarative.callbackmethod
    def reset_overload_cb(self):
        return

    @RELAY_EPICS.callback_add("UPLOAD")
    @declarative.callbackmethod
    def upload_sr560_cb(self):
        return

    @RELAY_EPICS.float_value_add("LOW_PASS_KNEE_N", precision=0, value=0)
    @declarative.dproperty
    def rv_low_pass_knee(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 15)
        )
        return rv

    @RELAY_EPICS.float_value_add("HIGH_PASS_KNEE_N", precision=0, value=0)
    @declarative.dproperty
    def rv_high_pass_knee(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 11)
        )
        return rv

    @RELAY_EPICS.float_value_add("VERNIER_GAIN", precision=0, value=0)
    @declarative.dproperty
    def rv_vernier_gain(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 100)
        )
        return rv

    @RELAY_EPICS.float_value_add("USEVERNIER", precision=0, value=0)
    @declarative.dproperty
    def rv_use_vernier(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 1)
        )
        return rv

    @RELAY_EPICS.float_value_add("INVERT", precision=0, value=0)
    @declarative.dproperty
    def rv_invert(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 1)
        )
        return rv

    @RELAY_EPICS.float_value_add("FILTER", precision=0, value=0)
    @declarative.dproperty
    def rv_filter(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 5)
        )
        return rv

    @RELAY_EPICS.float_value_add("INPUT", precision=0, value=0)
    @declarative.dproperty
    def rv_input(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 2)
        )
        return rv

    @RELAY_EPICS.float_value_add("COUPLING", precision=0, value=0)
    @declarative.dproperty
    def rv_coupling(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 2)
        )
        return rv

    @RELAY_EPICS.float_value_add("GAIN", precision=0, value=0)
    @declarative.dproperty
    def rv_gain(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 14)
        )
        return rv

    @RELAY_EPICS.float_value_add("DYNAMIC_RESERVE", precision=0, value=0)
    @declarative.dproperty
    def rv_dynamic_reserve(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, 2)
        )
        return rv
