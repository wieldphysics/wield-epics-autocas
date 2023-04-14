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
import YALL.controls.epics.panels as epics_panels

from YALL.controls.core.coroutine import reactor

from LabJackPython import LabJackException


class LJEbridge(epics.EpicsRelayUser):
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
            medm_template="LJ.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(LJEbridge, self).augment_medm(pvs_by_part, extra_replace, prefix=prefix)
        extra_replace["TITLE"] = self.display_name
        for iobr in self.IO_control_registry:
            iobr.augment_medm_prefixed(pvs_by_part, extra_replace, prefix)
        return

    @RELAY_EPICS.bool_add("ENABLE", buttons=True, binding_type="RW")
    @declarative.dproperty
    def state_enable(self):
        rbool = declarative.RelayBool(False)
        return rbool

    @RELAY_EPICS.bool_add("LJ_CONN", binding_type="W")
    @declarative.dproperty
    def state_LJ_connected(self):
        rbool = declarative.RelayBool(False)
        return rbool

    @RELAY_EPICS.float_value_add("SAMPLE_FREQ", precision=2, value=2, shadow=True)
    @declarative.dproperty
    def rv_sample_Hz(self):
        rv = declarative.RelayValue(2, declarative.min_max_validator(0.01, 128))
        return rv

    @RELAY_EPICS.float_value_add("SAMPLE_DIFF", precision=5, binding_type="RO")
    @declarative.dproperty
    def rv_sample_diff_t(self):
        rv = declarative.RelayValue(0)
        return rv

    @declarative.mproperty
    def IO_control_registry(self):
        return []

    @declarative.mproperty
    def medm_panel_io(self):
        lst = []
        for iobr in self.IO_control_registry:
            lst.append((iobr.order, iobr.prefix, iobr))
        lst.sort()

        panels = []
        for o, p, iobr in lst:
            panel = getattr(iobr, "medm_panel", None)
            if panel is not None:
                panels.append(panel)
        # print('IO: ', self.IO_control_registry)
        # print('PANELS: ', panels)
        medm = (
            epics_panels.HVNestedMEDM(
                [
                    panels[0::2],
                    panels[1::2],
                ],
                y_spacing=2,
            ),
        )
        return medm


class LJIOEBridge(epics.EpicsRelayUser):
    order = 0

    @declarative.dproperty
    def _setup_io_registry(self):
        self.parent.IO_control_registry.append(self)

    @declarative.dproperty
    def prefix(self, arg=declarative.NOARG):
        if arg is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return arg

    @declarative.dproperty
    def rv_connect_mode(self):
        # bind state connect so that this behaves like a true piece of the parent
        self.state_connect.bool_register(self.parent.state_connect)
        return self.parent.rv_connect_mode

    @declarative.dproperty
    def egroup(self, eg=declarative.NOARG):
        if eg is declarative.NOARG:
            raise RuntimeError("Must Specify")
        eg = eg.child(self.prefix)

        return eg

    def augment_medm_prefixed(self, pvs_by_part, extra_replace, prefix=""):
        self.augment_medm(
            pvs_by_part,
            extra_replace,
            prefix=prefix + "_" + self.prefix,
        )
        return


class LJADCEBridge(LJIOEBridge):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @RELAY_EPICS.float_value_add(
        "ADC", precision=3, value=0, burtRO=True, binding_type="RO"
    )
    @declarative.dproperty
    def rv_ADC(self):
        rv = declarative.RelayValue(0)
        return rv

    @declarative.mproperty
    def medm_panel(self):
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="LJ_ADC.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(LJADCEBridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["PREFIX"] = self.prefix
        return


class LJDACEBridge(LJIOEBridge):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @RELAY_EPICS.float_value_add(
        "DAC", precision=5, value=0, shadow=True, binding_type="pull"
    )
    @declarative.dproperty
    def rv_DAC(self):
        rv = declarative.RelayValue(0)
        return rv

    @declarative.mproperty
    def medm_panel(self):
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="LJ_DAC.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(LJDACEBridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["PREFIX"] = self.prefix
        return


class LJDoutEBridge(LJIOEBridge):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @RELAY_EPICS.float_value_add("DAC", precision=5, value=0, shadow=True)
    @declarative.dproperty
    def rv_DAC(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.bool_add("DOUT", buttons=True, binding_type="RW")
    @declarative.dproperty
    def state(self):
        rbool = declarative.RelayBool(False)
        return rbool

    @declarative.mproperty
    def medm_panel(self):
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="LJ_DOUT.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(LJDoutEBridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["PREFIX"] = self.prefix
        return


class LJDinEBridge(LJIOEBridge):
    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

    @RELAY_EPICS.bool_add("DIN", binding_type="W")
    @declarative.dproperty
    def state(self):
        rbool = declarative.RelayBool(False)
        return rbool

    @declarative.mproperty
    def medm_panel(self):
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="LJ_DIN.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(LJDinEBridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["PREFIX"] = self.prefix
        return


class LJRelay(
    contexts.AlertsUser,
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject,
):
    master_mode = True

    @staticmethod
    def construct_device():
        import u3

        return u3.U3()

    @declarative.dproperty
    def ebridge(self, ebr=declarative.NOARG):
        if ebr is declarative.NOARG:
            ebr = self
        ebr.rv_connect_mode.value = "master"
        ebr.state_connect.bool_register(self.state_connect_epics)
        return ebr

    @declarative.dproperty
    def serial_number(self, val=declarative.NOARG):
        if val is declarative.NOARG:
            val = None
        return val

    @declarative.dproperty
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
            reactor.send_task(
                lambda: self._connect_start(self._connection_token, first_try=True)
            )
        else:
            self._connection_token += 1
            reactor.send_task(
                lambda: self._connect_close(self._connection_token, finished=True)
            )
            return

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
            reactor.send_task(lambda: self._update(token))
        except LabJackException as e:
            if first_try:
                self.alerts.message_send_error("LJ missing: {0}".format(e))
            time = reactor.time()
            ntime = discrete_increment(time, 1, add=True)
            reactor.send_task(lambda: self._connect_start(token), ntime)

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
            reactor.send_task(lambda: self._connect_start(self._connection_token))

    def _update(self, token):
        if token != self._connection_token:
            return

        sample_period_s = 1 / self.ebridge.rv_sample_Hz.value
        time = reactor.time()
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

        reactor.send_task(lambda: self._update(token), ntime + sample_period_s)

    def LJ_cb_via(self, callback):
        try:
            # self._labjack may be None when not connected
            callback(self._labjack)
        except LabJackException as e:
            self.alerts.message_send_error("LJ lost: {0}".format(e))
            self._connect_close(self._connection_token)

    @declarative.mproperty
    def IO_direct_registry(self):
        return []

    @declarative.mproperty
    def IO_bits_registry(self):
        return []

    @declarative.mproperty
    def IO_raw_registry(self):
        return []


def discrete_increment(val, inc, add=False):
    if add:
        return val + inc - (val % inc)
    else:
        return val - (val % inc)


class LJIORelay(declarative.OverridableObject):
    ebridge = None
    parent = None
    use_type = "callback"

    @declarative.dproperty
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
