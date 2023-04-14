#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
TODO: Not finished
"""


from wield import declarative

import YALL.controls.core.contexts as contexts
import YALL.controls.epics as epics
import YALL.controls.epics.panels as epics_panels

from YALL.controls.core.churn_task import ChurnMethod


class SweeperEBridge(
    epics.EpicsRelayUser,
):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @RELAY_EPICS.bool_add("RUN", buttons=True, binding_type="RW")
    @declarative.dproperty
    def rb_state_sweep(self):
        rv = declarative.RelayBool(False)
        return rv

    @RELAY_EPICS.float_value_add("SAMP", precision=2, value=16, shadow=True)
    @declarative.dproperty
    def rv_sweep_sample(self):
        rv = declarative.RelayValue(
            16, validator=declarative.min_max_validator(0.0001, 128)
        )
        return rv

    @RELAY_EPICS.float_value_add("COUNT", precision=0, value=0, binding_type="ext")
    @declarative.dproperty
    def rv_sweep_count(self):
        rv = declarative.RelayValue(
            0, validator=declarative.min_max_validator_int(0, None)
        )
        return rv

    @RELAY_EPICS.float_value_add("RATE", precision=3, shadow=True)
    @declarative.dproperty
    def rv_sweep_rate(self):
        rv = declarative.RelayValue(
            10, validator=declarative.min_max_validator(0.0001, 100)
        )
        return rv

    @RELAY_EPICS.float_value_add("LOW", value=0, precision=2, shadow=True)
    @declarative.dproperty
    def rv_sweep_low(self):
        def validator(value):
            if value > self.rv_sweep_high.value:
                raise declarative.RelayValueRejected()
            return

        rv = declarative.RelayValue(0, validator=validator)
        return rv

    @RELAY_EPICS.float_value_add("HIGH", value=10, precision=2, shadow=True)
    @declarative.dproperty
    def rv_sweep_high(self):
        def validator(value):
            if value < self.rv_sweep_low.value:
                raise declarative.RelayValueRejected()
            return

        rv = declarative.RelayValue(10)
        return rv

    @RELAY_EPICS.float_value_add("OUT", precision=2, binding_type="ext")
    @declarative.dproperty
    def rv_sweep_mon(self):
        rv = declarative.RelayValue(0)
        return rv


class SweeperController(
    # epics.EpicsRelayUser,
    contexts.AlertsUser,
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject,
):
    # RELAY_EPICS = epics.RelayEpics((EpicsRelayUser.RELAY_EPICS,))

    @declarative.dproperty
    def ebridge(self, ebr):
        ebr.rv_connect_mode.value = "master"
        ebr.state_connect.bool_register(self.state_connect_epics)
        return ebr

    @declarative.dproperty
    def _sweep_setup(self):
        self.ebridge.rb_state_sweep.register(
            callback=self._sweep_cb,
            assumed_value=False,
        )

    _sweep_val_prev = None

    def _sweep_cb(self, bstate):
        if bstate:
            self._sweep_task = ChurnMethod()
            self._sweep_task(self._sweep_update)
        else:
            self._sweep_task.cancel()
            self._sweep_val_prev = None

    def _sweep_update(self, task):
        update_s = 1 / self.ebridge.rv_sweep_sample.value
        val = self.ebridge.rv_sweep_mon.value
        ntime = discrete_increment(task.time(), update_s, add=True)
        # print("sweep!", val, task.time())
        if self._sweep_val_prev is None:
            d_low = abs(val - self.ebridge.rv_sweep_low.value)
            d_high = abs(val - self.ebridge.rv_sweep_high.value)
            if d_low < d_high:
                self.ebridge.rv_sweep_mon.value = (
                    val + self.ebridge.rv_sweep_rate.value * update_s
                )
            else:
                self.ebridge.rv_sweep_mon.value = (
                    val - self.ebridge.rv_sweep_rate.value * update_s
                )
        elif self._sweep_val_prev < val:
            # going up
            nval = val + self.ebridge.rv_sweep_rate.value * update_s
            if nval > self.ebridge.rv_sweep_high.value:
                nval = val - self.ebridge.rv_sweep_rate.value * update_s
                self.ebridge.rv_sweep_count.value += 1
            self.ebridge.rv_sweep_mon.value = nval
        else:
            # going down
            nval = val - self.ebridge.rv_sweep_rate.value * update_s
            if nval < self.ebridge.rv_sweep_low.value:
                nval = val + self.ebridge.rv_sweep_rate.value * update_s
                self.ebridge.rv_sweep_count.value += 1
            self.ebridge.rv_sweep_mon.value = nval
        self._sweep_val_prev = val
        task(self._sweep_update, ntime)


def discrete_increment(val, inc, add=False):
    if add:
        return val + inc - (val % inc)
    else:
        return val - (val % inc)
