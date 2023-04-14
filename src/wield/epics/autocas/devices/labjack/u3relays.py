#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


from wield import declarative as decl

import u3

from .service import LJIORelay


class LJU3ADCRelay(LJIORelay):
    use_type = "bits"

    posChannel = None
    negChannel = 31
    longSettle = False
    quickSample = False

    clear_val = None

    def setup(self, lj):
        if self.negChannel not in [31, 32, None]:
            lj.configAnalog(self.posChannel, self.negChannel)
        else:
            lj.configAnalog(self.posChannel)

    def clear(self):
        if self.clear_val is not None:
            self.ebridge.rv_ADC.value = self.clear_val
        return

    def interface(self, lj):
        self.ebridge.rv_ADC.value = lj.getAIN(
            posChannel=self.posChannel,
            negChannel=self.negChannel,
            longSettle=self.longSettle,
            quickSample=self.quickSample,
        )
        return

    def bits_write(self, lj):
        """Split the getAIN method of u3 into the two sections for this"""
        if self.negChannel == 32:
            # part of being isSpecial in the read section
            negChannel = 30
        else:
            negChannel = self.negChannel
        return u3.AIN(self.posChannel, negChannel, self.longSettle, self.quickSample)

    def bits_read(self, lj, bits):
        """Split the getAIN method of u3 into the two sections for this"""
        if self.negChannel == 32:
            isSpecial = True
        else:
            isSpecial = False

        if self.negChannel != 31:
            singleEnded = False
        else:
            singleEnded = True

        if lj.deviceName.endswith("-HV") and self.posChannel < 4:
            lvChannel = False
        else:
            lvChannel = True

        self.ebridge.rv_ADC.value = lj.binaryToCalibratedAnalogVoltage(
            bits,
            isLowVoltage=lvChannel,
            isSingleEnded=singleEnded,
            isSpecialSetting=isSpecial,
            channelNumber=self.posChannel,
        )
        return


class LJU3DACRelay(LJIORelay):
    use_type = "callback"

    dacChannel = None
    is16Bits = True

    def setup(self, lj):
        if self.dacChannel == 1:
            lj.configU3(DAC1Enable=True)

    @decl.dproperty
    def callback_setup(self):
        self.parent.ebridge.state_LJ_connected.register_via(
            self.ebridge.rv_DAC.register,
            callback=self._DAC_val_change_cb,
            call_immediate=True,
        )

    def _DAC_val_change_cb(self, value):
        def send(lj):
            if lj is None:
                return
            value_raw = lj.voltageToDACBits(
                value,
                self.dacChannel,
                self.is16Bits,
            )

            if self.is16Bits:
                bits = u3.DAC16(self.dacChannel, value_raw)
            else:
                bits = u3.DAC8(self.dacChannel, value_raw)
            lj.getFeedback(bits)
            return

        self.parent.LJ_cb_via(send)
        return

    def bits_write(self, lj):
        value_raw = lj.voltageToDACBits(
            self.ebridge.rv_DAC.value,
            self.dacChannel,
            self.is16Bits,
        )

        if self.is16Bits:
            bits = u3.DAC16(self.dacChannel, value_raw)
        else:
            bits = u3.DAC8(self.dacChannel, value_raw)
        return bits

    def bits_read(self, lj, bits):
        return


class LJU3DOUTRelay(LJIORelay):
    use_type = "bits"

    dChannel = None

    def setup(self, lj):
        lj.configDigital(self.dChannel)
        lj.getFeedback(u3.BitDirWrite(self.dChannel, 1))

    def bits_write(self, lj):
        return u3.BitStateWrite(self.dChannel, bool(self.ebridge.state))

    def bits_read(self, lj, bits):
        return


class LJU3DINRelay(LJIORelay):
    use_type = "bits"

    dChannel = None
    clear_val = None

    def clear(self):
        if self.clear_val is not None:
            self.ebridge.state.assign(self.clear_val)
        return

    def setup(self, lj):
        lj.configDigital(self.dChannel)
        lj.getFeedback(u3.BitDirWrite(self.dChannel, 0))

    def bits_write(self, lj):
        return u3.BitStateRead(self.dChannel)

    def bits_read(self, lj, bits):
        self.ebridge.state.assign(bits)
        return
