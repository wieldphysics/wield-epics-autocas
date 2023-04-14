#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


import sys
from .. import cascore
from ..serial import SerialError


class SerialUser(
    cascore.CASUser,
):
    "Must be hosted by a IFR2026"

    @cascore.dproperty
    def serial(self):
        return self.parent.serial

    @cascore.dproperty
    def SBlist_readbacks(self):
        return []

    @cascore.dproperty
    def SBlist_setters(self):
        return []

    @cascore.dproperty
    def SB_parent(self, val=None):
        """
        Parent serial-block
        """
        return val


class SerialDevice(SerialUser):
    @cascore.dproperty
    def serial(self, val=None):
        if val is None:
            val = self.parent.serial
        return val

    @cascore.dproperty
    def rb_autoset(self):
        rb = cascore.RelayBool(False)
        self.cas_host(
            rb,
            "AUTOSET",
            interaction="setting",
            urgentsave_s=10,
        )
        return rb

    @cascore.dproperty
    def _onconnect_setup(self):
        def connect_cb(value):
            if value:
                if self.rb_autoset:
                    for RB in self.SBlist_setters:
                        RB()
                for RB in self.SBlist_readbacks:
                    RB()
                self.reactor.send_task(self.serial.run)
                return

        self.serial.rb_connected.register(
            callback=connect_cb,
        )
        return

    @cascore.dproperty_ctree(default=None)
    def device_SN(self, val):
        """
        Serial number of the device to check via *IDN? call.
        ID command Must succeed to attempt future commands and SN must match if specified
        """
        if val == "":
            val = None
        return val

    @cascore.dproperty
    def block_root(self):
        def action_sequence(cmd):
            with self.serial.error.clear_pending():
                try:
                    cmd.block_remainder()
                except SerialError as E:
                    self.serial.error(1, str(E))
                    print(self, "ERROR", str(E))
                    self.serial.rb_communicating.put(False)
                except Exception as E:
                    self.serial.error(0, str(E))
                    print(self, "ERROR", str(E))
                    self.serial.rb_communicating.put(False)
                    raise
                else:
                    self.serial.rb_communicating.put(True)

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            name="root",
            prefix=self.prefix,
        )
        return block

    @cascore.dproperty
    def SB_SN_id_check(self):
        def action_sequence(cmd):
            cmd.writeline("*IDN?")
            val = cmd.readline()
            SN_found = val.strip()
            if self.device_SN is not None:
                if SN_found != self.device_SN:
                    print(
                        "Warning, device expected {0} but device found: {1}".format(
                            self.device_SN, SN_found
                        ),
                        file=sys.stderr,
                    )
                    raise SerialError("Wrong Device")
            try:
                with self.serial.error.clear_pending():
                    cmd.block_remainder()
            finally:
                pass

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.block_root,
            name="id_check",
            prefix=self.prefix,
        )
        return block
