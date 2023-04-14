#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


import numpy as np
from ... import cascore

# from ..serial import SerialError
from ..serial_device import SerialDevice, SerialUser


class TEK_AFG3000(SerialDevice):
    @cascore.dproperty
    def chn1(self):
        chn = TEK_AFG3000_Chn(
            parent=self,
            SB_parent=self.SB_SN_id_check,
            name="chn1",
            device_channel_name="1",
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn

    @cascore.dproperty
    def chn2(self):
        chn = TEK_AFG3000_Chn(
            parent=self,
            SB_parent=self.SB_SN_id_check,
            name="chn2",
            device_channel_name="2",
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn


class TEK_AFG3000_Chn(SerialUser):
    "Must be hosted by a"

    @cascore.dproperty
    def device_channel_name(self, val):
        return val

    @cascore.dproperty
    def FM(self):
        fm = TEK_AFG3000_FM(
            parent=self,
            name="FM",
            SB_parent=self.SB_parent,
        )
        self.SBlist_setters.extend(fm.SBlist_setters)
        self.SBlist_readbacks.extend(fm.SBlist_readbacks)
        return

    #############################
    # RF FREQUENCY
    #############################
    @cascore.dproperty_ctree(default=10e3)
    def frequency_limit_low(self, val):
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=1.4e9)
    def frequency_limit_high(self, val):
        assert val > 0
        return val

    @cascore.dproperty
    def rv_frequency_set(self):
        default = self.ctree.get_configured(
            "frequency_set",
            default=100e6,
        )

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
            cmd.writeline(
                "SOURCE{0}:FREQ:CW {1:f}Hz".format(
                    self.device_channel_name, self.rv_frequency_set.value
                )
            )
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
        def action_sequence(cmd):
            cmd.writeline(
                "SOURCE{0}:FREQ:CW?".format(
                    self.device_channel_name, self.rv_frequency_set.value
                )
            )
            response = cmd.readline()
            self.rv_frequency_RB.value = float(response)

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
    # RF PHASE
    #############################
    @cascore.dproperty_ctree(default=-180)
    def phase_limit_low(self, val):
        assert val >= -180
        return val

    @cascore.dproperty_ctree(default=180)
    def phase_limit_high(self, val):
        assert val <= 360
        return val

    @cascore.dproperty
    def rv_phase_set(self):
        default = self.ctree.get_configured("phase_set", default=0)

        rv = cascore.RelayValueFloatLowHighMod(
            default,
            low=self.phase_limit_low,
            high=self.phase_limit_high,
        )

        self.cas_host(
            rv,
            "phase_set",
            interaction="setting",
            urgentsave_s=10,
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_phase_set(self):
        def action_sequence(cmd):
            cmd.writeline(
                "SOURCE{0}:PHAS {1:f}".format(
                    self.device_channel_name, self.rv_phase_set.value * np.pi / 180.0
                )
            )
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="phase_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_phase_RB)
        self.SBlist_setters.append(block)

        self.rv_phase_set.register(callback=block)

        return block

    @cascore.dproperty
    def rv_phase_RB(self):
        default = self.ctree.get_configured(
            "phase_RB",
            default=-1,
            about="phase readback default (used when value unavailable)",
        )
        rv = cascore.RelayValueFloat(default)
        self.cas_host(
            rv,
            "PHASE_RB",
            interaction="report",
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_phase_RB(self):
        def action_sequence(cmd):
            cmd.writeline(
                "SOURCE{0}:PHASE?".format(
                    self.device_channel_name, self.rv_phase_set.value
                )
            )
            response = cmd.readline()
            self.rv_phase_RB.value = float(response) * 180 / np.pi

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="phase_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ##############################
    ## RF LEVEL
    ##############################

    @cascore.dproperty_ctree(default=-35)
    def level_dbm_limit_low(self, val):
        """
        low limit of RF Output level in dbm
        """
        assert val >= -35
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
            "level_dbm_set", default=-35, about="default RF level"
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
            cmd.writeline(
                "SOURCE{0}:VOLTage:LEVel:IMMediate:AMPLitude {1:f}DBM".format(
                    self.device_channel_name, level_dbm
                )
            )
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
        def action_sequence(cmd):
            cmd.writeline("SOURCE{0}:VOLTage:UNIT DBM".format(self.device_channel_name))
            cmd.writeline(
                "SOURCE{0}:VOLTage:LEVel:IMMediate:AMPLitude?".format(
                    self.device_channel_name
                )
            )
            response = cmd.readline()
            self.rv_level_dbm_RB.value = float(response)

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="level_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ######################################
    ##  RF Output ON/OFF
    ######################################

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
                cmd.writeline("OUTPUT{0}:STATe ON".format(self.device_channel_name))
            else:
                cmd.writeline("OUTPUT{0}:STATe OFF".format(self.device_channel_name))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="output_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_output_RB)
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

    @cascore.dproperty
    def SB_output_RB(self):
        def action_sequence(cmd):
            cmd.writeline("OUTPUT{0}:STATe?".format(self.device_channel_name))
            response = cmd.readline()
            # bool will check if string is 0, length so convert to int first for 0/1 check
            self.rb_output_RB.value = bool(int(response))

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="output_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ################################
    ## Modulation type
    ################################

    @cascore.dproperty
    def rv_mod_type_set(self):
        rv = cascore.RelayValueEnum(0, ["OFF", "AM", "FM", "PM"])
        self.cas_host(
            rv,
            "MOD_TYPE",
            interaction="setting",
        )
        return rv

    @cascore.dproperty
    def SB_mod_type_set(self):
        def action_sequence(cmd):
            if self.rv_mod_type_set.value_str == "OFF":
                cmd.writeline(
                    "SOURCE{0}:FREQuency:MODE CW".format(self.device_channel_name)
                )
            else:
                cmd.writeline(
                    "SOURCE{0}:{1}:STATE ON".format(
                        self.device_channel_name, self.rv_mod_type_set.value_str
                    )
                )
            self.SB_mod_func_RB()
            self.SB_mod_source_RB()

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_type_RB",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_mod_type_RB)
        self.SBlist_setters.append(block)
        self.rv_mod_type_set.register(callback=block)
        return block

    @cascore.dproperty
    def rv_mod_type_RB(self):
        rv = cascore.RelayValueEnum(0, ["OFF", "AM", "FM", "PM"])
        self.cas_host(
            rv,
            "MOD_TYPE_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_type_RB(self):
        def action_sequence(cmd):
            type = 0
            for mod in self.rv_mod_type_RB.state2int:
                if mod != "OFF":
                    cmd.writeline(
                        "SOURCE{0}:{1}:STATE?".format(self.device_channel_name, mod)
                    )
                    if int(cmd.readline()):
                        type = self.rv_mod_type_RB.state2int[mod]

            self.rv_mod_type_RB.value = type

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_type_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ######################################
    ##  MODULATION SOURCE (internal/external)
    ######################################
    @cascore.dproperty
    def rv_mod_source_set(self):
        rv = cascore.RelayValueEnum(0, ["INT", "EXT"])
        self.cas_host(
            rv,
            "MOD_SOURCE",
            interaction="setting",
        )
        return rv

    @cascore.dproperty
    def SB_mod_source_set(self):
        def action_sequence(cmd):
            if self.rv_mod_type_set.value_str != "OFF":
                cmd.writeline(
                    "SOURCE{0}:{1}:SOURCE {2}".format(
                        self.device_channel_name,
                        self.rv_mod_type_set.value_str,
                        self.rv_mod_source_set.value_str,
                    )
                )
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_source_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_mod_source_RB)
        self.SBlist_setters.append(block)
        self.rv_mod_source_set.register(callback=block)
        return block

    @cascore.dproperty
    def rv_mod_source_RB(self):
        rv = cascore.RelayValueEnum(0, ["INT", "EXT"])
        self.cas_host(
            rv,
            "mod_source_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_source_RB(self):
        def action_sequence(cmd):
            if self.rv_mod_type_set.value_str != "OFF":
                cmd.writeline(
                    "SOURCE{0}:{1}:SOURCE?".format(
                        self.device_channel_name, self.rv_mod_type_set.value_str
                    )
                )
                response = cmd.readline()
            else:
                response = "INT"

            self.rv_mod_source_RB.value = self.rv_mod_source_RB.state2int[response]

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="mod_source_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ################################
    ## Modulation mode (if internal)
    ################################

    @cascore.dproperty
    def rv_mod_func_set(self):
        rv = cascore.RelayValueEnum(0, ["SIN", "SQU", "TRI", "RAMP"])
        self.cas_host(
            rv,
            "MOD_FUNC",
            interaction="setting",
        )
        return rv

    @cascore.dproperty
    def SB_mod_func_set(self):
        def action_sequence(cmd):
            if self.rv_mod_type_set.value_str != "OFF":
                cmd.writeline(
                    "SOURCE{0}:{1}:INTernal:FUNCtion {2}".format(
                        self.device_channel_name,
                        self.rv_mod_type_set.value_str,
                        self.rv_mod_func_set.value_str,
                    )
                )

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_func_RB",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_mod_func_RB)
        self.SBlist_setters.append(block)
        self.rv_mod_func_set.register(callback=block)
        return block

    @cascore.dproperty
    def rv_mod_func_RB(self):
        rv = cascore.RelayValueEnum(0, ["SIN", "SQU", "TRI", "RAMP"])
        self.cas_host(
            rv,
            "MOD_FUNC_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_func_RB(self):
        def action_sequence(cmd):
            if self.rv_mod_type_set.value_str != "OFF":
                cmd.writeline(
                    "SOURCE{0}:{1}:INTernal:FUNCtion?".format(
                        self.device_channel_name, self.rv_mod_type_set.value_str
                    )
                )
                response = cmd.readline()
                self.rv_mod_func_RB.value = self.rv_mod_func_RB.state2int[response]
            else:
                self.rv_mod_func_RB.value = 0

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_func_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block


class TEK_AFG3000_FM(SerialUser):
    """
    Must be hosted by a TEK_AFG3000Channel
    """

    @cascore.dproperty_ctree(default=1)
    def FM_fdev_limit_low(self, val):
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=100e3)
    def FM_fdev_limit_high(self, val):
        assert val > 0
        return val

    ##############################
    ## RF FM_FDEV
    ##############################
    @cascore.dproperty
    def rv_FM_fdev_set(self):
        default = self.ctree.get_configured("FM_fdev_set", default=10e3)

        rv = cascore.RelayValueFloatLowHighMod(
            default,
            low=self.FM_fdev_limit_low,
            high=self.FM_fdev_limit_high,
            modulo=1,
        )

        self.cas_host(
            rv,
            "FDEV",
            interaction="setting",
            urgentsave_s=10,
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_fdev_set(self):
        def action_sequence(cmd):
            cmd.writeline(
                "SOURCE{0}:FM:DEViation {1:f}Hz".format(
                    self.parent.device_channel_name, self.rv_FM_fdev_set.value
                )
            )
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="fdev_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_fdev_RB)
        self.SBlist_setters.append(block)
        self.rv_FM_fdev_set.register(callback=block)
        return block

    @cascore.dproperty
    def rv_FM_fdev_RB(self):
        default = self.ctree.get_configured(
            "fdev_RB",
            default=-1,
            about="FM fdev readback default (used when value unavailable)",
        )
        rv = cascore.RelayValueFloat(default)
        self.cas_host(
            rv,
            "FDEV_RB",
            interaction="report",
            prec=3,
        )
        return rv

    @cascore.dproperty
    def SB_fdev_RB(self):
        def action_sequence(cmd):
            cmd.writeline(
                "SOURCE{0}:FM:DEViation?".format(self.parent.device_channel_name)
            )
            response = cmd.readline()
            self.rv_FM_fdev_RB.value = float(response)

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="fdev_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block
