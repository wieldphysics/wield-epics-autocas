#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
Name: EI1050
Desc: A few simple classes to handle communication with the EI1050 probe
"""

from wield import declarative

import u3
import u6
import ue9

from .service import LJIORelay
from YALL.controls.core.churn_task import ChurnMethod


class EI1050relay(LJIORelay):
    """
    EI1050 class to simplify communication with an EI1050 probe
    """

    use_type = "callback"

    dataPinNum = None
    clockPinNum = None
    enablePinNum = None
    shtOptions = 0xC0

    ebridge_temp = None
    ebridge_humidity = None

    read_period_s = 10

    def setup(self, lj):
        self._deviceMod = {
            "U3": u3,
            "U6": u6,
            "UE9": ue9,
        }[lj.__class__.__name__]

        # if self._deviceMod is u3:
        # Set U3 pins
        # lj.configIO(FIOAnalog = 0)
        if self.enablePinNum is not None:
            lj.configDigital(self.enablePinNum)
            lj.getFeedback(self._deviceMod.BitDirWrite(self.enablePinNum, 1))

    @declarative.dproperty
    def callback_setup(self):
        self.parent.ebridge.state_LJ_connected.register(
            callback=self._connect_cb,
            assumed_value=False,
        )

    def _connect_cb(self, bstate):
        if bstate:
            self._task = ChurnMethod()
            ntime = discrete_increment(self._task.time(), self.read_period_s, add=True)
            self._task(self._update_task, ntime)
        else:
            self._task.cancel()

    def _update_task(self, task):
        self.parent.LJ_cb_via(self.interface)
        ntime = discrete_increment(task.time(), self.read_period_s, add=True)
        task(self._update_task, ntime)
        return

    def clear(self):
        return

    def interface(self, lj):
        """
        Name: EI1050.update()
        Desc: Gets a fresh set of readings from this probe
        """
        import time

        t1 = time.time()
        self.write_bit_state(lj, self.enablePinNum, 1)  # Enable the probe
        state = lj.sht1x(self.dataPinNum, self.clockPinNum, self.shtOptions)
        self.write_bit_state(lj, self.enablePinNum, 0)  # Disable the probe
        try:
            self.ebridge_temp.rv_ADC.value = state["Temperature"]
            self.ebridge_humidity.rv_ADC.value = state["Humidity"]
        except Exception as e:
            print("EI1050 error: ", e)
        t2 = time.time()
        # print "TIME: ", t2-t1
        return

    def write_bit_state(self, lj, pinNum, state):
        """
        Name: EI1050.write_bit_state(pinNum, state)
        Desc: Device independent way to write bit state
        """
        if pinNum is not None:
            if self._deviceMod is not ue9:
                lj.getFeedback(self._deviceMod.BitStateWrite(pinNum, state))
            else:
                lj.singleIO(1, pinNum, Dir=1, State=state)


def discrete_increment(val, inc, add=False):
    if add:
        return val + inc - (val % inc)
    else:
        return val - (val % inc)
