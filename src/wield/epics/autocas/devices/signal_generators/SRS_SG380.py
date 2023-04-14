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
from ... import cascore
from ...serial import SerialError
from ..serial_device import SerialDevice, SerialUser


class SRS_SG380(SerialDevice):
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

    @cascore.dproperty
    def chn(self):
        chn = SRS_SG380_Chn(
            parent=self,
            SB_parent=self.SB_SN_id_check,
            name="chn",
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn


class SRS_SG380_Chn(SerialUser):
    "Must be hosted by a IFR2026"

    @cascore.dproperty
    def FM(self):
        fm = SRS_SG380_FM(
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
            cmd.writeline("FREQ {0:f}Hz".format(self.rv_frequency_set.value))
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
            cmd.writeline("FREQ?")
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
            cmd.writeline("AMPR {0:f}".format(level_dbm))
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
            cmd.writeline("AMPR?")
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
                cmd.writeline("ENBR 1")
            else:
                cmd.writeline("ENBR 0")
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
            cmd.writeline("ENBR?")
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

    ###############################
    # Modulation type
    ###############################

    @cascore.dproperty
    def rv_mod_type_set(self):
        rv = cascore.RelayValueEnum(
            1, ["AM", "FM", "PM", "SWEEP", "Pulse", "blank", "IQ"]
        )
        self.cas_host(
            rv,
            "MOD_TYPE",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_type_set(self):
        def action_sequence(cmd):
            cmd.writeline("TYPE {0}".format(self.rv_mod_type_set.value))

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
        rv = cascore.RelayValueEnum(
            7, ["AM", "FM", "PM", "SWEEP", "Pulse", "blank", "IQ", "unknown"]
        )
        self.cas_host(
            rv,
            "MOD_TYPE_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_type_RB(self):
        def action_sequence(cmd):
            cmd.writeline("TYPE?")
            response = cmd.readline()
            self.rv_mod_type_RB.value = int(response)

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_type_RB",
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
                cmd.writeline("MODL 1")
            else:
                cmd.writeline("MODL 0")
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
        def action_sequence(cmd):
            cmd.writeline("MODL?")
            response = cmd.readline()
            # bool will check if string is 0, length so convert to int first for 0/1 check
            self.rb_mod_status_RB.value = bool(int(response))

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="mod_status_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block


class SRS_SG380_FM(SerialUser):
    """
    Must be hosted by a SRS_SG380Channel
    """

    @cascore.dproperty_ctree(default=1)
    def FM_fdev_limit_low(self, val):
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=100e3)
    def FM_fdev_limit_high(self, val):
        assert val > 0
        return val

    #############################
    # RF FM_FDEV
    #############################
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
            cmd.writeline("FDEV {0:f}".format(self.rv_FM_fdev_set.value))
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
            cmd.writeline("FDEV?")
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

    #############################
    # RF FM_DEVN
    #############################

    @cascore.dproperty_ctree(default=1)
    def FM_devn_limit_low(self, val):
        assert val > 0
        return val

    @cascore.dproperty_ctree(default=100e3)
    def FM_devn_limit_high(self, val):
        assert val > 0
        return val

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
            cmd.writeline("FNDV {0:f}".format(self.rv_FM_devn_set.value))
            return

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="devn_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_devn_RB)
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
    def SB_devn_RB(self):
        def action_sequence(cmd):
            cmd.writeline("FNDV?")
            response = cmd.readline()
            self.rv_FM_devn_RB.value = float(response)

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="devn_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    @cascore.dproperty
    def rv_coupling_set(self):
        rv = cascore.RelayValueEnum(1, ["AC", "DC"])
        self.cas_host(
            rv,
            "CPLG",
            interaction="setting",
            urgentsave_s=10,
        )
        return rv

    @cascore.dproperty
    def SB_coupling_set(self):
        def action_sequence(cmd):
            cmd.writeline("COUP {0}".format(self.rv_coupling_set.value))

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="coupling_set",
            prefix=self.prefix,
        )
        self.serial.block_chain(block, self.SB_coupling_RB)
        self.SBlist_setters.append(block)
        self.rv_coupling_set.register(callback=block)
        return block

    @cascore.dproperty
    def rv_coupling_RB(self):
        rv = cascore.RelayValueEnum(2, ["AC", "DC", "unknown"])
        self.cas_host(
            rv,
            "CPLG_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_coupling_RB(self):
        def action_sequence(cmd):
            cmd.writeline("COUP?")
            response = cmd.readline()
            self.rv_coupling_RB.put_coerce(int(response))

        block = self.serial.block_add(
            action_sequence,
            ordering=10,
            parent=self.SB_parent,
            name="coupling_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block

    ###############################
    # Modulation mode
    ###############################

    @cascore.dproperty
    def rv_mod_func_set(self):
        rv = cascore.RelayValueEnum(
            5, ["sine", "ramp", "triangle", "square", "noise", "ext"]
        )
        self.cas_host(
            rv,
            "MOD_FUNC",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_func_set(self):
        def action_sequence(cmd):
            cmd.writeline("MFNC {0}".format(self.rv_mod_func_set.value))

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
        rv = cascore.RelayValueEnum(
            6, ["sine", "ramp", "triangle", "square", "noise", "ext", "unknown"]
        )
        self.cas_host(
            rv,
            "MOD_FUNC_RB",
            interaction="report",
        )
        return rv

    @cascore.dproperty
    def SB_mod_func_RB(self):
        def action_sequence(cmd):
            cmd.writeline("MFNC?")
            response = cmd.readline()
            self.rv_mod_func_RB.value = int(response)

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            parent=self.SB_parent,
            name="mod_func_RB",
            prefix=self.prefix,
        )
        self.SBlist_readbacks.append(block)
        return block
