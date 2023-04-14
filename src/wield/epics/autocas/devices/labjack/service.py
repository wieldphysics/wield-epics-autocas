#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


from wield.epics import autocas
import socket

from LabJackPython import LabJackException


class LJRelay(autocas.OverridableObject):
    @staticmethod
    def construct_device():
        import u3

        return u3.U3()

    @autocas.dproperty
    def serial_number(self, val=autocas.NOARG):
        if val is autocas.NOARG:
            val = None
        return val

    @autocas.dproperty
    def state_enable(self):
        rbool = self.ebridge.state_enable
        rbool.register(
            callback=self._state_enable_do,
            assumed_value=False,
        )
        self._connection_token = 0
        return rbool

    def _state_enable_do(self, bval):
        if bval:
            self._connection_token += 1
            self.reactor.send_task(
                lambda: self._connect_start(self._connection_token, first_try=True)
            )
        else:
            self._connection_token += 1
            self.reactor.send_task(
                lambda: self._connect_close(self._connection_token, finished=True)
            )
            return

    # @RELAY_EPICS.bool_add('LJ_CONN', binding_type = 'W')
    @autocas.dproperty
    def state_LJ_connected(self):
        rbool = autocas.RelayBool(False)
        return rbool

    # @RELAY_EPICS.float_value_add('SAMPLE_FREQ', precision = 2, value = 2, shadow = True)
    @autocas.dproperty
    def rv_sample_Hz(self):
        rv = autocas.RelayValue(2, autocas.min_max_validator(0.01, 128))
        return rv

    # @RELAY_EPICS.float_value_add('SAMPLE_DIFF', precision = 5, binding_type = 'RO')
    @autocas.dproperty
    def rv_sample_diff_t(self):
        rv = autocas.RelayValue(0)
        return rv

    @autocas.mproperty
    def IO_control_registry(self):
        return []

    _labjack = None

    def _connect_start(self, token, first_try=False):
        if token != self._connection_token:
            return

        try:
            if self.serial_number is None:
                self._labjack = self.construct_device()
                self._labjack.getCalibrationData()
                for iorelay in self.IO_direct_registry:
                    iorelay.setup(self._labjack)
                for iorelay in self.IO_bits_registry:
                    iorelay.setup(self._labjack)
            else:
                raise NotImplementedError()

            self.alerts.message_send_action("connected to LJ")
            self.ebridge.state_LJ_connected.assign(True)
            self.reactor.send_task(lambda: self._update(token))
        except LabJackException as e:
            if first_try:
                self.alerts.message_send_error("LJ missing: {0}".format(e))
            time = self.reactor.time()
            ntime = discrete_increment(time, 1, add=True)
            self.reactor.send_task(lambda: self._connect_start(token), ntime)
        except (socket.timeout, socket.error) as e:
            if first_try:
                self.alerts.message_send_error("LJ socket timout: {0}".format(e))
            time = self.reactor.time()
            ntime = discrete_increment(time, 1, add=True)
            self.reactor.send_task(lambda: self._connect_start(token), ntime)

    def _connect_close(self, token, finished=False):
        if token != self._connection_token:
            return
        if self._labjack is not None:
            try:
                self._labjack.close()
            except LabJackException:
                pass
            self._labjack = None

        for iorelay in self.IO_direct_registry:
            iorelay.clear()
        for iorelay in self.IO_bits_registry:
            iorelay.clear()
        for iorelay in self.IO_raw_registry:
            iorelay.clear()

        self.ebridge.state_LJ_connected.assign(False)
        self._connection_token += 1

        if not finished:
            self.reactor.send_task(lambda: self._connect_start(self._connection_token))

    def _update(self, token):
        if token != self._connection_token:
            return

        sample_period_s = 1 / self.ebridge.rv_sample_Hz.value
        time = self.reactor.time()
        # print("UPDATE: ", time)
        ntime = discrete_increment(time, sample_period_s)
        self.ebridge.rv_sample_diff_t.value = time - ntime

        try:
            for iorelay in self.IO_direct_registry:
                iorelay.interface(self._labjack)
            if self.IO_bits_registry:
                bits = []
                for iorelay in self.IO_bits_registry:
                    bits.append(iorelay.bits_write(self._labjack))
                bits_out = self._labjack.getFeedback(bits)
                for idx, iorelay in enumerate(self.IO_bits_registry):
                    iorelay.bits_read(self._labjack, bits_out[idx])
            if self.IO_raw_registry:
                # raw_write = []
                rnums = []
                read_current = 0
                for idx, iorelay in enumerate(self.IO_raw_registry):
                    wbits, rnum = iorelay.raw_write(self._labjack)
                    # raw_write.extend(wbits)
                    self._labjack.write(wbits)
                    rnums.append(rnum)
                    if idx - read_current >= 1:
                        retbits = self._labjack.read(rnums[read_current])
                        self.IO_raw_registry[read_current].raw_read(
                            self._labjack, retbits
                        )
                        read_current += 1
                while read_current < len(self.IO_raw_registry):
                    retbits = self._labjack.read(rnums[read_current])
                    self.IO_raw_registry[read_current].raw_read(self._labjack, retbits)
                    read_current += 1

        except LabJackException as e:
            self.alerts.message_send_error("LJ lost: {0}".format(e))
            self._connect_close(token)
        except (socket.timeout, socket.error) as e:
            self.alerts.message_send_error("LJ socket timout: {0}".format(e))
            self._connect_close(token)

        self.reactor.send_task(lambda: self._update(token), ntime + sample_period_s)

    def LJ_cb_via(self, callback):
        try:
            # self._labjack may be None when not connected
            callback(self._labjack)
        except LabJackException as e:
            self.alerts.message_send_error("LJ lost: {0}".format(e))
            self._connect_close(self._connection_token)
        except (socket.timeout, socket.error) as e:
            self.alerts.message_send_error("LJ socket timout: {0}".format(e))
            self._connect_close(self._connection_token)

    @autocas.mproperty
    def IO_direct_registry(self):
        return []

    @autocas.mproperty
    def IO_bits_registry(self):
        return []

    @autocas.mproperty
    def IO_raw_registry(self):
        return []


class LJIORelayBase(autocas.OverridableObject):
    use_type = "callback"

    @autocas.dproperty
    def _setup_io_registry(self):
        if self.use_type == "interface":
            self.parent.IO_direct_registry.append(self)
        elif self.use_type == "bits":
            self.parent.IO_bits_registry.append(self)
        elif self.use_type == "raw":
            self.parent.IO_raw_registry.append(self)
        elif self.use_type == "callback":
            pass
        else:
            raise RuntimeError("Bad Interface Spec")

    def setup(self, lj):
        return

    def clear(self):
        return


class LJADCEBridge(LJIORelayBase):
    # @RELAY_EPICS.string_value_add('LABEL')
    @autocas.dproperty
    def rv_label(self):
        rv = autocas.RelayValue("")
        return rv

    # @RELAY_EPICS.float_value_add('ADC', precision = 3, value = 0, burtRO = True, binding_type = 'RO')
    @autocas.dproperty
    def rv_ADC(self):
        rv = autocas.RelayValue(0)
        return rv


class LJDACEBridge(LJIORelayBase):
    # @RELAY_EPICS.string_value_add('LABEL')
    @autocas.dproperty
    def rv_label(self):
        rv = autocas.RelayValue("")
        return rv

    # @RELAY_EPICS.float_value_add('DAC', precision = 5, value = 0, shadow = True, binding_type = 'pull')
    @autocas.dproperty
    def rv_DAC(self):
        rv = autocas.RelayValue(0)
        return rv


class LJDoutEBridge(LJIORelayBase):

    # @RELAY_EPICS.string_value_add('LABEL')
    @autocas.dproperty
    def rv_label(self):
        rv = autocas.RelayValue("")
        return rv

    # @RELAY_EPICS.float_value_add('DAC', precision = 5, value = 0, shadow = True)
    @autocas.dproperty
    def rv_DAC(self):
        rv = autocas.RelayValue(0)
        return rv

    # @RELAY_EPICS.bool_add('DOUT', buttons = True, binding_type = 'RW')
    @autocas.dproperty
    def state(self):
        rbool = autocas.RelayBool(False)
        return rbool


class LJDinEBridge(LJIORelayBase):
    # @RELAY_EPICS.string_value_add('LABEL')
    @autocas.dproperty
    def rv_label(self):
        rv = autocas.RelayValue("")
        return rv

    # @RELAY_EPICS.bool_add('DIN', binding_type = 'W')
    @autocas.dproperty
    def state(self):
        rbool = autocas.RelayBool(False)
        return rbool
