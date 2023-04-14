#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


import re

from ... import cascore
from ...serial import SerialError
from ..serial_device import SerialUser


float_re = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"


class IFRSigGenChannel(SerialUser):
    "Must be hosted by a IFR2026 or IFR 2023"

    #############################
    # RF PHASE
    #############################
    @cascore.dproperty
    def rv_phase_shift(self):
        rv = cascore.RelayValueFloatLowHighMod(
            0,
            low  = -180,
            high = +180,
            modulo = 0.1,
        )

        self.cas_host(
            rv,
            'phase_shift',
            interaction = "command",
            prec       = 1,
        )
        return rv

    @cascore.dproperty
    def SB_phase_shift(self):
        def action_sequence(cmd):
            cmd.writeline(':CFRQ:PHASE {0:f}'.format(self.rv_phase_shift.value))
            #now reset the shift ammount
            self.rv_phase_shift.value = 0
            return

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'phase_shift',
            prefix = self.prefix,
        )
        self.SBlist_setters.append(block)

        self.rv_phase_shift.register(callback = block)
        return block

    @cascore.dproperty
    def FM(self):
        fm = IFRSigGenChannelFM(
            parent=self,
            name="FM",
            SB_parent=self.SB_parent,
        )
        self.SBlist_setters.extend(fm.SBlist_setters)
        self.SBlist_readbacks.extend(fm.SBlist_readbacks)
        return

    @cascore.dproperty_ctree(default=10e3)
    def frequency_limit_low(self, val):
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=1.4e9)
    def frequency_limit_high(self, val):
        assert val > 0
        return val

    #############################
    # RF FREQUENCY
    #############################
    @cascore.dproperty
    def rv_frequency_set(self):
        default = self.ctree.get_configured("frequency_set", default=100e6)

        rv = cascore.RelayValueFloatLowHighMod(
            default,
            low=self.frequency_limit_low,
            high=self.frequency_limit_high,
            modulo=1,
        )

        self.cas_host(
            rv,
            "freq_set",
            interaction="setting",
            urgentsave_s=10,
            prec=6,
        )
        return rv

    @cascore.dproperty
    def SB_freq_set(self):
        def action_sequence(cmd):
            cmd.writeline(":CFRQ:VALUE {0:f}Hz".format(self.rv_frequency_set.value))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="freq_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_freq_RB)
        self.SBlist_setters.append(block)

        self.rv_frequency_set.register(callback=block)

        return block

    @cascore.dproperty
    def rv_frequency_RB(self):
        default = self.ctree.get_configured(
            "frequency_RB",
            default=-1,
            about="frequency readback default (used when value unavailable)",
        )
        rv = cascore.RelayValueFloat(default)
        self.cas_host(
            rv,
            "FREQ_RB",
            interaction="report",
            prec=6,
        )
        return rv

    @cascore.dproperty
    def SB_freq_RB(self):
        # two groups 0: the frequency in Hz 1: The increment in Hz
        # the last group allows parsing 2026 and 2023 return values
        re_FREQVALUE = re.compile(
            "^:CFRQ:VALUE ({0});INC ({0})(?:|;MODE FIXED)$".format(float_re)
        )

        def action_sequence(cmd):
            cmd.writeline("CFRQ?")
            response = cmd.readline()
            match = re_FREQVALUE.match(response)
            if not match:
                raise SerialError("Frequency Request: {0}".format(response))
            self.rv_frequency_RB.value = float(match.group(1))

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="freq_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    #############################
    # RF LEVEL
    #############################
    @cascore.dproperty_ctree(default=-120)
    def level_dbm_limit_low(self, val):
        """
        low limit of RF Output level in dbm
        """
        assert val >= -120
        return val

    @cascore.dproperty_ctree(default=-10)
    def level_dbm_limit_high(self, val):
        """
        high limit of RF Output level in dbm (This can damage equipment to be too high! Be conservative here)
        """
        assert val <= 20
        return val

    @cascore.dproperty
    def rv_level_dbm_set(self):
        default = self.ctree.get_configured(
            "level_dbm_set", default=-120, about="default RF level"
        )

        rv = cascore.RelayValueFloatLowHighMod(
            default,
            low=self.level_dbm_limit_low,
            high=self.level_dbm_limit_high,
            modulo=0.01,
        )

        self.cas_host(
            rv,
            "level_set",
            interaction="setting",
            urgentsave_s=10,
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_level_set(self):
        def action_sequence(cmd):
            level_dbm = self.rv_level_dbm_set.value
            if level_dbm > self.level_dbm_limit_high:
                print(level_dbm, self.level_dbm_limit_high)
                raise RuntimeError("RF Level above limit!")
            cmd.writeline(":RFLV:UNITS DBM;:RFLV:VALUE {0:.3f}DBM".format(level_dbm))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="level_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_level_RB)
        self.SBlist_setters.append(block)
        self.rv_level_dbm_set.register(callback=block)

        return block

    @cascore.dproperty
    def rv_level_dbm_RB(self):
        default = self.ctree.get_configured(
            "level_dbm_RB",
            default=-1,
            about="level_dbm readback default (used when value unavailable)",
        )
        rv = cascore.RelayValueFloat(default)
        self.cas_host(
            rv,
            "level_RB",
            interaction="report",
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_level_RB(self):
        re_LEVELVALUE = re.compile(
            "^:RFLV:UNITS DBM;TYPE (PD|EMF);VALUE ({0});INC {0};(ON|OFF)$".format(
                float_re
            )
        )

        def action_sequence(cmd):
            cmd.writeline("RFLV?")
            response = cmd.readline()
            match = re_LEVELVALUE.match(response)
            if not match:
                raise SerialError("Level_dbm Request: {0}".format(response))

            level_dbm = float(match.group(2))
            level_on = {"ON": True, "OFF": False}[match.group(3)]

            self.rv_level_dbm_RB.value = level_dbm
            self.rb_output_RB.value = level_on

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="level_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    #####################################
    #  RF Output ON/OFF
    #####################################
    @cascore.dproperty
    def rb_output_set(self):
        default = self.ctree.get_configured(
            "output_set", default=False, about="default for activating RF output"
        )

        rv = cascore.RelayBool(default)

        self.cas_host(
            rv,
            "output_set",
            interaction="setting",
            urgentsave_s=10,
        )
        return rv

    @cascore.dproperty
    def SB_output_set(self):
        def action_sequence(cmd):
            if self.rb_output_set:
                cmd.writeline(":RFLV:ON")
            else:
                cmd.writeline(":RFLV:OFF")
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="output_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_level_RB)
        self.SBlist_setters.append(block)
        self.rb_output_set.register(callback=block)
        return block

    @cascore.dproperty
    def rb_output_RB(self):
        default = self.ctree.get_configured(
            "output_RB",
            default=True,
            about="output status readback default (used when value unavailable)",
        )
        rv = cascore.RelayBool(default)
        self.cas_host(
            rv,
            "output_RB",
            interaction="report",
        )
        return rv

    ###############################
    # Modulation Mode
    ###############################

    @cascore.dproperty
    def rv_modmode_RB(self):
        rv = cascore.RelayValueString("")
        self.cas_host(
            rv,
            "MODMODE_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_modmode_RB(self):
        def action_sequence(cmd):
            cmd.writeline("MODE?")
            response = cmd.readline()
            self.rv_modmode_RB.value = response

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="modmode_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ###############################
    # Modulation Status
    ###############################
    @cascore.dproperty
    def rb_mod_status_set(self):
        default = self.ctree.get_configured(
            "modulation_status",
            default=False,
            about="default for activating modulation",
        )

        rv = cascore.RelayBool(default)

        self.cas_host(
            rv,
            "MODSTAT",
            interaction="setting",
            urgentsave_s=10,
        )
        return rv

    @cascore.dproperty
    def SB_mod_status_set(self):
        def action_sequence(cmd):
            if self.rb_mod_status_set:
                cmd.writeline(":MOD:ON")
            else:
                cmd.writeline(":MOD:OFF")
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_status_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_mod_status_RB)
        self.SBlist_setters.append(block)
        self.rb_mod_status_set.register(callback=block)
        return block

    @cascore.dproperty
    def rb_mod_status_RB(self):
        rb = cascore.RelayBool(False)
        self.cas_host(
            rb,
            "MODSTAT_RB",
            interaction="report",
        )
        return rb

    @cascore.dproperty
    def SB_mod_status_RB(self):
        # three groups 0: EMF type (not used) 1: output level in DBM 2: output power state
        re_MODSTAT = re.compile("^:MOD:(ON|OFF)$")

        def action_sequence(cmd):
            cmd.writeline("MOD?")
            response = cmd.readline()
            match = re_MODSTAT.match(response)
            if not match:
                raise SerialError("mod status request: {0}".format(response))

            mod_on = {"ON": True, "OFF": False}[match.group(1)]
            self.rb_mod_status_RB.value = mod_on

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="mod_status_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block


class IFRSigGenChannelFM(SerialUser):
    """
    Must be hosted by a IFRSigGenChannel
    """

    @cascore.dproperty_ctree(default=1)
    def FM_devn_limit_low(self, val):
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=100e3)
    def FM_devn_limit_high(self, val):
        assert val > 0
        return val

    #############################
    # RF FM_DEVN
    #############################
    @cascore.dproperty
    def rv_FM_devn_set(self):
        default = self.ctree.get_configured("FM_devn_set", default=10e3)

        rv = cascore.RelayValueFloatLowHighMod(
            default,
            low=self.FM_devn_limit_low,
            high=self.FM_devn_limit_high,
            modulo=1,
        )

        self.cas_host(
            rv,
            "DEVN",
            interaction="setting",
            urgentsave_s=10,
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_devn_set(self):
        def action_sequence(cmd):
            cmd.writeline(":FM:DEVN {0:f}Hz".format(self.rv_FM_devn_set.value))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="devn_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_FM_RB)
        self.SBlist_setters.append(block)
        self.rv_FM_devn_set.register(callback=block)
        return block

    @cascore.dproperty
    def rv_FM_devn_RB(self):
        default = self.ctree.get_configured(
            "devn_RB",
            default=-1,
            about="FM devn readback default (used when value unavailable)",
        )
        rv = cascore.RelayValueFloat(default)
        self.cas_host(
            rv,
            "DEVN_RB",
            interaction="report",
            prec=3,
        )
        return rv

    @cascore.dproperty
    def rv_coupling_RB(self):
        rv = cascore.RelayValueEnum(0, ["INT", "EXTAC", "EXTALC", "EXTDC"])
        self.cas_host(
            rv,
            "CPLG_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_FM_RB(self):
        # two groups 0: the frequency devn in Hz, 1: the coupling mode; 2: the local on/off; 3: the increment value
        re_DEVNVALUE = re.compile(
            "^:FM:DEVN ({0});(INT|EXTAC|EXTALC|EXTDC)\s*;(ON|OFF)\s*;INC ({0})$".format(
                float_re
            )
        )

        def action_sequence(cmd):
            cmd.writeline("FM?")
            response = cmd.readline()
            match = re_DEVNVALUE.match(response)
            if not match:
                raise SerialError("FM Query: {0}".format(response))

            self.rv_FM_devn_RB.value = float(match.group(1))
            self.rv_coupling_RB.put_coerce(match.group(2))
            self.rb_FM_mod_status_RB.value = {"ON": True, "OFF": False}[match.group(3)]

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="FM_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ###############################
    # Modulation Status
    ###############################
    @cascore.dproperty
    def rb_mod_status_set(self):
        default = self.ctree.get_configured(
            "modulation_status",
            default=False,
            about="default for activating modulation",
        )

        rv = cascore.RelayBool(default)

        self.cas_host(
            rv,
            "MODSTAT",
            interaction="setting",
            urgentsave_s=10,
        )
        return rv

    @cascore.dproperty
    def SB_mod_status_set(self):
        def action_sequence(cmd):
            if self.rb_mod_status_set:
                cmd.writeline(":FM:ON")
            else:
                cmd.writeline(":FM:OFF")
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_status_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_FM_RB)
        self.SBlist_setters.append(block)
        self.rb_mod_status_set.register(callback=block)
        return block

    @cascore.dproperty
    def rb_FM_mod_status_RB(self):
        rb = cascore.RelayBool(False)
        self.cas_host(
            rb,
            "MODSTAT_RB",
            interaction="report",
        )
        return rb
