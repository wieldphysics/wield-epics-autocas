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
import re

from ... import cascore
from ...serial import SerialError
from ..serial_device import SerialDevice
from . import IFRSigGenCommon


class IFR2026(SerialDevice):
    @cascore.dproperty
    def chnA(self):
        chn = IFR2026Channel(
            parent=self,
            name="chnA",
            device_channel_name="A",
            SB_parent=self.SB_SN_id_check,
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn

    @cascore.dproperty
    def chnB(self):
        chn = IFR2026Channel(
            parent=self,
            name="chnB",
            device_channel_name="B",
            SB_parent=self.SB_SN_id_check,
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn

    # @cascore.dproperty
    # def lockout_soft(self):
    #    """
    #    Sends soft (front panel) lockout signal when using rs232.
    #    """
    #    def action_sequence(cmd):
    #        #special character to activate local lockout
    #        cmd.writeline(chr(01))
    #        for i in range(30):
    #            cmd.writeline('*TST?')
    #            resp = cmd.readline(timeout_s = 0.02)
    #            if resp:
    #                break

    #    block = self.serial.block_add(
    #        action_sequence,
    #        ordering = -1,
    #        parent = self.SB_SN_id_check,
    #        name = 'lockout_soft',
    #        prefix = self.prefix,
    #    )
    #    return block


class IFR2026Channel(
    cascore.CASUser,
):
    """
    Must be hosted by a IFR2026
    """

    @cascore.dproperty
    def serial(self):
        return self.parent.serial

    @cascore.dproperty
    def SBlist_readbacks(self):
        return self.channel.SBlist_readbacks

    @cascore.dproperty
    def SBlist_setters(self):
        return self.channel.SBlist_setters

    @cascore.dproperty
    def SB_parent(self, val):
        """
        Parent serial-block
        """
        return val

    @cascore.dproperty
    def device_channel_name(self, val):
        return val

    @cascore.dproperty
    def SB_set_chn(self):
        # one group, the channel name
        re_SOURCE = re.compile("^:SOURCE (.)$")

        def action_sequence(cmd):
            cmd.writeline(":SOURCE {0};:SOURCE?".format(self.device_channel_name))
            response = cmd.readline()
            match = re_SOURCE.match(response)
            if not match:
                raise SerialError("Channel Set Response: {0}".format(response))
            response_chn = match.group(1)
            if response_chn != self.device_channel_name:
                raise SerialError("Channel Not Set by request")

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="set_chn",
            prefix=self.prefix,
        )
        return block

    @cascore.dproperty
    def channel(self):
        return IFRSigGenCommon.IFRSigGenChannel(
            parent=self,
            SB_parent=self.SB_set_chn,
            name="channel",
            subprefix=None,
        )
