#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
import sys as sysmod
import contextlib
from wield import declarative

from YALL.controls import epics
from YALL.controls.core import contexts

from YALL.controls.core.oldtools.relay_bool_coupler import (
    RelayBoolEpics,
)


class SR560ConnectionEBridge(epics.EpicsCarrier):
    pass


class SR560SerialService(
    epics.EpicsCarrier,
    contexts.ToplevelActive,
    contexts.EpicsConnectable,
):
    @declarative.dproperty
    def ebridge_service(self, ebridge=declarative.NOARG):
        if ebridge is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return ebridge

    @declarative.dproperty
    def serial_address(self, val=declarative.NOARG):
        if val is declarative.NOARG:
            val = "/dev/ttyS0"
        return val

    @declarative.dproperty
    def rbool_epics(self, ebool=declarative.NOARG):
        if ebool is declarative.NOARG:
            ebool = RelayBoolEpics(
                egroup=self.egroup.child("BE"),
                parent=self,
            )
        return ebool

    @declarative.dproperty
    def postfix(self, val=declarative.NOARG):
        if val is declarative.NOARG:
            val = None
        return val

    @declarative.dproperty
    def display_name(self, val=declarative.NOARG):
        if val is declarative.NOARG:
            val = "SR560 Serial"
            if self.postfix is not None:
                val = val + " For " + self.postfix
        return val

    @declarative.dproperty
    def state_active(self, rbool=declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBoolAll()
        rbool.bool_register(self.state_active_toplevel)
        rbool.bool_register(self.state_enable)
        rbool.register(callback=self._state_active_do, assumed_value=False)
        return rbool

    @declarative.dproperty
    def state_fake(self):
        rbool = declarative.RelayBool(False)
        return rbool

    tty_F = None

    def _state_active_do(self, bstate):
        if bstate:
            if not self.state_fake:
                try:
                    import serial

                    self.tty_F = serial.Serial(
                        self.serial_address,
                        baudrate=9600,
                        stopbits=2,
                        timeout=1,
                        writeTimeout=1,
                    )
                    self.state_connected.assign(True)
                except ImportError:
                    print("Couldn't Import python serial module, going to fake state")
                    self.state_fake.assign(True)
                except IOError as e:
                    print(
                        "Error starting SR560 serial connection: ",
                        e,
                        " going to fake state",
                    )
                    self.state_fake.assign(True)
            if self.state_fake:
                self.tty_F = sysmod.stdout
                self.state_connected.assign(True)
        else:
            if self.tty_F is not sysmod.stdout:
                self.tty_F.close()
                self.tty_F = None
            self.state_connected.assign(False)

    @declarative.dproperty
    def state_enable(self):
        rbool = declarative.RelayBool(False)
        self.rbool_epics.bool_view_set("ENABLE", rbool, settable=True)
        self.rbool_epics.bool_button_set("ENABLE", rbool)
        return rbool

    @declarative.dproperty
    def state_connected(self, rbool=declarative.NOARG):
        if rbool is declarative.NOARG:
            rbool = declarative.RelayBool(False)
        self.rbool_epics.bool_view_set("CONNECTED", rbool)
        return rbool

    @declarative.dproperty
    def medm_panel(self):
        # return SR560ConnectionPanel(system = self)
        medm = epics.MEDMSystemScreen(
            system=self,
            relpath=__file__,
            medm_template="SR560_CONNECTION.adl",
        )
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        # super(SR560SerialService, self).augment_medm(pvs_by_part, extra_replace, prefix = prefix)
        self.rbool_epics.augment_medm(pvs_by_part, extra_replace)
        extra_replace["TITLE"] = self.display_name
        return


class SR560Relay(
    contexts.EpicsConnectable, contexts.ParentCarrier, declarative.OverridableObject
):
    master_mode = True

    @declarative.dproperty
    def ebridge(self, ebr=declarative.NOARG):
        if ebr is declarative.NOARG:
            ebr = self
        ebr.rv_connect_mode.value = "master"
        ebr.state_connect.bool_register(self.state_connect_epics)
        return ebr

    @declarative.dproperty
    def serial_service(self, rct=declarative.NOARG):
        if rct is declarative.NOARG:
            raise RuntimeError("Must Specify")
        return rct

    @declarative.dproperty
    def device_addr(self, num=declarative.NOARG):
        if num is declarative.NOARG:
            num = None
        return num

    @declarative.dproperty
    def state_serial_connected(self):
        rbool = self.serial_service.state_connected
        rbool.register_via(
            self.ebridge.reset_overload_cb.register,
            callback=self._reset_overload_send,
        )
        rbool.register_via(
            self.ebridge.upload_sr560_cb.register,
            callback=self._upload_all_send,
        )
        return rbool

    @declarative.dproperty
    def state_autoload_connected(self):
        rbool = declarative.RelayBoolAll()
        rbool.bool_register(self.state_serial_connected)
        rbool.bool_register(self.ebridge.state_autoload)
        rbool.register_via(
            self.ebridge.rv_low_pass_knee.register,
            callback=self._low_pass_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_high_pass_knee.register,
            callback=self._high_pass_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_coupling.register,
            callback=self._input_coupling_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_input.register,
            callback=self._input_source_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_filter.register,
            callback=self._filter_mode_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_invert.register,
            callback=self._invert_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_use_vernier.register,
            callback=self._use_vernier_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_vernier_gain.register,
            callback=self._vernier_gain_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_gain.register,
            callback=self._gain_send,
            call_immediate=True,
        )
        rbool.register_via(
            self.ebridge.rv_dynamic_reserve.register,
            callback=self._dynamic_reserve_send,
            call_immediate=True,
        )
        return rbool

    _addressing_depth = 0

    @contextlib.contextmanager
    def address_my_sr560(self):
        if self._addressing_depth == 0:
            if self.device_addr is None:
                self.serial_service.tty_F.write("LALL\r\n")
            else:
                self.serial_service.tty_F.write(
                    "LISN {0}\r\n".format(int(self.device_addr))
                )
        self._addressing_depth += 1
        yield
        self._addressing_depth -= 1
        return

    def _upload_all_send(self):
        with self.address_my_sr560():
            self._low_pass_send(self.ebridge.rv_low_pass_knee.value)
            self._high_pass_send(self.ebridge.rv_high_pass_knee.value)
            self._gain_send(self.ebridge.rv_gain.value)
            self._dynamic_reserve_send(self.ebridge.rv_dynamic_reserve.value)
            self._input_coupling_send(self.ebridge.rv_coupling.value)
            self._input_source_send(self.ebridge.rv_input.value)
            self._filter_mode_send(self.ebridge.rv_filter.value)
            self._invert_send(self.ebridge.rv_invert.value)
            self._use_vernier_send(self.ebridge.rv_use_vernier.value)
            self._vernier_gain_send(self.ebridge.rv_vernier_gain.value)
        return

    def _low_pass_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("LFRQ {0}\r\n".format(int(value)))
        return

    def _high_pass_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("HFRQ {0}\r\n".format(int(value)))
        return

    def _reset_overload_send(self):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("ROLD\r\n")
        return

    def _input_source_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("SRCE {0}\r\n".format(int(value)))
        return

    def _use_vernier_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("UCAL {0}\r\n".format(int(value)))
        return

    def _vernier_gain_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("UCGN {0}\r\n".format(int(value)))
        return

    def _invert_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("INVT {0}\r\n".format(int(value)))
        return

    def _gain_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("GAIN {0}\r\n".format(int(value)))
        return

    def _dynamic_reserve_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("DYNR {0}\r\n".format(int(value)))
        return

    def _filter_mode_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("FLTM {0}\r\n".format(int(value)))
        return

    def _input_coupling_send(self, value):
        with self.address_my_sr560():
            self.serial_service.tty_F.write("CPLG {0}\r\n".format(int(value)))
        return
