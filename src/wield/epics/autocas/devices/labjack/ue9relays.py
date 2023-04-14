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

import ue9

from . import service


class LJUE9ADCRelay(service.LJIORelay):
    # use_type = 'interface'
    use_type = "raw"

    posChannel = None
    clear_val = None

    BipGain = 0x00
    Resolution = 12
    SettlingTime = 0

    def setup(self, lj):
        pass

    def clear(self):
        if self.clear_val is not None:
            self.rv_ADC.value = self.clear_val
        return

    def interface(self, lj):
        self.rv_ADC.value = lj.getAIN(
            self.posChannel,
            BipGain=self.BipGain,
            Resolution=self.Resolution,
            SettlingTime=self.SettlingTime,
        )
        return

    def raw_write(self, lj):
        """Split the getAIN method of u3 into the two sections for this"""
        command = [
            0,  # #command[0] = Checksum8
            0xA3,  # command[1] = 0xA3
            4,  # command[2] = IOType
            self.posChannel,  # command[3] = Channel
            ##Analog In
            self.BipGain,  # command[4] = BipGain
            self.Resolution,  # command[5] = Resolution
            self.SettlingTime,  # command[6] = SettlingTime
            0,
        ]
        return command, 8

    def raw_read(self, lj, result):
        """Split the getAIN method of u3 into the two sections for this"""
        assert result[2] == 4
        # Analog In
        ain = float((result[6] << 16) + (result[5] << 8) + result[4]) / 256

        self.rv_ADC.value = lj.binaryToCalibratedAnalogVoltage(
            ain, self.BipGain, self.Resolution
        )
        return


class LJUE9TempRelay(LJUE9ADCRelay):
    posChannel = 133

    def interface(self, lj):
        self.rv_ADC.value = lj.getTemperature()
        return

    def raw_read(self, lj, result):
        """Split the getAIN method of u3 into the two sections for this"""
        assert result[2] == 4
        # Analog In
        ain = float((result[6] << 16) + (result[5] << 8) + result[4]) / 256

        self.rv_ADC.value = lj.binaryToCalibratedAnalogTemperature(
            ain, self.BipGain, self.Resolution
        )
        return


class LJUE9DACRelay(service.LJIORelay):
    use_type = "callback"

    dacChannel = None
    is16Bits = True

    def setup(self, lj):
        pass

    def interface(self, lj):
        # MAY NOT WORK WITH USB
        if self.dacChannel == 0:
            lj.writeRegister(5000, self.rv_DAC.value)
        elif self.dacChannel == 1:
            lj.writeRegister(5002, self.rv_DAC.value)
        return

    @decl.dproperty
    def callback_setup(self):
        self.parent.ebridge.state_LJ_connected.register_via(
            self.rv_DAC.register,
            callback=self._DAC_val_change_cb,
            call_immediate=True,
        )

    def _DAC_val_change_cb(self, value):
        def send(lj):
            if lj is None:
                return
            # MAY NOT WORK WITH USB
            if self.dacChannel == 0:
                lj.writeRegister(5000, value)
            elif self.dacChannel == 1:
                lj.writeRegister(5002, value)
            return

        self.parent.LJ_cb_via(send)
        return


# not yet implemented
# class LJUE9DOUTRelay(service.LJIORelay):
#    use_type = 'bits'
#
#    dChannel  = None
#
#    def setup(self, lj):
#        lj.configDigital(self.dChannel)
#        lj.getFeedback(ue9.BitDirWrite(self.dChannel, 1))
#
#    def bits_write(self, lj):
#        return ue9.BitStateWrite(self.dChannel, bool(self.state))
#
#    def bits_read(self, lj, bits):
#        return
#
# class LJUE9DINRelay(service.LJIORelay):
#    use_type = 'bits'
#
#    dChannel  = None
#    clear_val = None
#
#    def clear(self):
#        if self.clear_val is not None:
#            self.state.assign(self.clear_val)
#        return
#
#    def setup(self, lj):
#        lj.configDigital(self.dChannel)
#        lj.getFeedback(ue9.BitDirWrite(self.dChannel, 0))
#
#    def bits_write(self, lj):
#        return ue9.BitStateRead(self.dChannel)
#
#    def bits_read(self, lj, bits):
#        self.state.assign(bits)
#        return


class UE9Device(service.LJRelay):
    adc_set = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    dac_set = [0, 1]

    @staticmethod
    def construct_device():
        return ue9.UE9(ipAddress="192.168.0.21", ethernet=True)

    @decl.dproperty
    def DAC_io(self):
        return [
            LJUE9DACRelay(
                ebridge=self.ebridge.DAC_map[0],
                parent=self,
                dacChannel=0,
            ),
            LJUE9DACRelay(
                ebridge=self.ebridge.DAC_map[1],
                parent=self,
                dacChannel=1,
            ),
        ]

    @decl.dproperty
    def ADC_io(self):
        ADC_map = dict()
        for chn, ebr in self.ebridge.ADC_map.items():
            ADC_map[chn] = (
                LJUE9ADCRelay(
                    ebridge=ebr,
                    parent=self,
                    posChannel=chn,
                    clear_val=-8888.8888,
                ),
            )
        return ADC_map
