#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


from ... import cascore
from . import IFRSigGenCommon
from ..serial_device import SerialDevice


class IFR2023(SerialDevice):
    @cascore.dproperty
    def chn(self):
        chn = IFRSigGenCommon.IFRSigGenChannel(
            parent=self,
            SB_parent=self.SB_SN_id_check,
            name="chn",
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
