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
    declarative.dproperty, declarative.mproperty, declarative.NOARG,
)


from YALL.controls.peripherals.labjack.service import (
    LJEbridge,
    LJRelay,
    LJADCEBridge,
    LJDACEBridge,
    LJDinEBridge,
    LJDoutEBridge,
)


from YALL.controls.peripherals.labjack.u3relays import (
    LJU3ADCRelay,
    LJU3DACRelay,
    LJU3DOUTRelay,
    LJU3DINRelay,
)

class SHGLJU3EBridge(LJEbridge):
    adc_set   = [0, 1, 2, 3, "p4n5", "p6n7"]
    dac_set   = [0, 1]
    d_out_set = [8, 9]
    d_in_set  = [10, 11]

    @declarative.dproperty
    def ADC_map(self):
        ebr_map = dict()
        for k in self.adc_set:
            adc_ebr = LJADCEBridge(
                egroup = self.egroup,
                order  = 0,
                prefix = str(k),
                parent = self,
            )
            ebr_map[k] = adc_ebr
        return ebr_map

    @declarative.dproperty
    def DAC_map(self):
        ebr_map = dict()
        for k in self.dac_set:
            adc_ebr = LJDACEBridge(
                egroup = self.egroup,
                order  = -1,
                prefix = str(k),
                parent = self,
            )
            ebr_map[k] = adc_ebr
        return ebr_map

    @declarative.dproperty
    def DOUT_map(self):
        ebr_map = dict()
        for k in self.d_out_set:
            adc_ebr = LJDoutEBridge(
                egroup = self.egroup,
                order  = 1,
                prefix = str(k),
                parent = self,
            )
            ebr_map[k] = adc_ebr
        return ebr_map

    @declarative.dproperty
    def DIN_map(self):
        ebr_map = dict()
        for k in self.d_in_set:
            adc_ebr = LJDinEBridge(
                egroup = self.egroup,
                order  = 2,
                prefix = str(k),
                parent = self,
            )
            ebr_map[k] = adc_ebr
        return ebr_map


class SHGLJU3Relay(LJRelay):
    @staticmethod
    def construct_device():
        import u3
        return u3.U3()

    @declarative.dproperty
    def DAC_io(self):
        return [
            LJU3DACRelay(
                ebridge    = self.ebridge.DAC_map[0],
                parent     = self,
                dacChannel = 0,
            ),
            LJU3DACRelay(
                ebridge    = self.ebridge.DAC_map[1],
                parent     = self,
                dacChannel = 1,
            ),
        ]

    @declarative.dproperty
    def ADC_io(self):
        return [
            LJU3ADCRelay(
                ebridge    = self.ebridge.ADC_map[0],
                parent     = self,
                posChannel = 0,
                clear_val  = float('inf'),
            ),
            LJU3ADCRelay(
                ebridge    = self.ebridge.ADC_map[1],
                parent     = self,
                posChannel = 1,
            ),
            LJU3ADCRelay(
                ebridge    = self.ebridge.ADC_map[2],
                parent     = self,
                posChannel = 2,
            ),
            LJU3ADCRelay(
                ebridge    = self.ebridge.ADC_map[3],
                parent     = self,
                posChannel = 3,
            ),
            LJU3ADCRelay(
                ebridge    = self.ebridge.ADC_map['p4n5'],
                parent     = self,
                posChannel = 4,
                negChannel = 5,
            ),
            LJU3ADCRelay(
                ebridge    = self.ebridge.ADC_map['p6n7'],
                parent     = self,
                posChannel = 6,
                negChannel = 7,
            ),
        ]
    @declarative.dproperty
    def DOUT_io(self):
        return [
            LJU3DOUTRelay(
                ebridge  = self.ebridge.DOUT_map[8],
                parent   = self,
                dChannel = 8,
            ),
            LJU3DOUTRelay(
                ebridge  = self.ebridge.DOUT_map[9],
                parent   = self,
                dChannel = 9,
            ),
        ]
    @declarative.dproperty
    def DIN_io(self):
        return [
            LJU3DINRelay(
                ebridge  = self.ebridge.DIN_map[10],
                parent   = self,
                dChannel = 10,
            ),
            LJU3DINRelay(
                ebridge  = self.ebridge.DIN_map[11],
                parent   = self,
                dChannel = 11,
            ),
        ]
