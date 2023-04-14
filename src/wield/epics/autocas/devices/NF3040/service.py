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
from YALL.controls import epics
from YALL.controls.epics import panels as epics_panels
from YALL.controls.core import processes
from YALL.controls.core import contexts

from . import tempController


class NF3040Ebridge(epics.EpicsRelayUser):
    """ """

    RELAY_EPICS = epics.RelayEpics((epics.EpicsRelayUser.RELAY_EPICS,))

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
            medm_template="NF3040.adl",
        )
        medm.medm_screen_filename_from_namechain(self.egroup.name_chain.child("PANEL"))
        return medm

    @declarative.mproperty
    def medm_full_panel(self):
        medm = epics_panels.VHNestedMEDM(
            [
                self.process.medm_panel,
                self.medm_panel,
            ]
        )
        medm.medm_screen_filename_from_namechain(self.egroup.name_chain.child("FPANEL"))
        return medm

    def augment_medm(self, pvs_by_part, extra_replace, prefix=""):
        super(NF3040Ebridge, self).augment_medm(
            pvs_by_part, extra_replace, prefix=prefix
        )
        extra_replace["TITLE"] = self.display_name
        return

    @declarative.dproperty
    def process(self):
        return processes.SubscriptEBridge(
            parent=self,
            egroup=self.egroup.child("PRC"),
            display_name="tempController.py",
        )

    @RELAY_EPICS.bool_add("CONNECT", binding_type="RW")
    @declarative.dproperty
    def connection_mon(self):
        rb = declarative.RelayBool(False)
        return rb

    @RELAY_EPICS.float_value_add("TSET", precision=3)
    @declarative.dproperty
    def temp_set(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("TSET_MON", precision=3, binding_type="push")
    @declarative.dproperty
    def temp_set_mon(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("TMEAS", precision=3, binding_type="push")
    @declarative.dproperty
    def temp_measured(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.string_value_add("GAIN")
    @declarative.dproperty
    def gain(self):
        rv = declarative.RelayValue("20S")
        return rv

    @RELAY_EPICS.string_value_add("GAIN_MON", binding_type="push")
    @declarative.dproperty
    def gain_mon(self):
        rv = declarative.RelayValue("<unknown>")
        return rv

    @RELAY_EPICS.float_value_add("ILIM", precision=3)
    @declarative.dproperty
    def current_limit(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("ILIM_MON", precision=3, binding_type="push")
    @declarative.dproperty
    def current_limit_mon(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("IOUT", precision=3, binding_type="push")
    @declarative.dproperty
    def current_out_measured(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("ISET", precision=3)
    @declarative.dproperty
    def current_out_set(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("ISET_MON", precision=3, binding_type="push")
    @declarative.dproperty
    def current_out_set_mon(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("RMEAS", precision=3, binding_type="push")
    @declarative.dproperty
    def R_measured(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.string_value_add("MODE")
    @declarative.dproperty
    def mode(self):
        rv = declarative.RelayValue("")
        return rv

    @RELAY_EPICS.string_value_add("MODE_MON", binding_type="push")
    @declarative.dproperty
    def mode_mon(self):
        rv = declarative.RelayValue("<unknown>")
        return rv

    @RELAY_EPICS.bool_add("OUT_EN", buttons=True, binding_type="RW")
    @declarative.dproperty
    def out_enable(self):
        rb = declarative.RelayBool(False)
        return rb

    @RELAY_EPICS.bool_add("OUT_EN_MON", binding_type="RW")
    @declarative.dproperty
    def out_enable_mon(self):
        rb = declarative.RelayBool(False)
        return rb

    @RELAY_EPICS.float_value_add("TMIN", precision=3)
    @declarative.dproperty
    def temp_min(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("TMIN_MON", precision=3, binding_type="push")
    @declarative.dproperty
    def temp_min_mon(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("TMAX", precision=3)
    @declarative.dproperty
    def temp_max(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.float_value_add("TMAX_MON", precision=3, binding_type="push")
    @declarative.dproperty
    def temp_max_mon(self):
        rv = declarative.RelayValue(0)
        return rv

    @RELAY_EPICS.bool_add("LOCAL", buttons=True, binding_type="RW")
    @declarative.dproperty
    def local_control(self):
        rb = declarative.RelayBool(False)
        return rb


class NF3040Runner(
    contexts.AlertsUser,
    contexts.EpicsConnectable,
    contexts.ParentCarrier,
    declarative.OverridableObject,
):
    script_name = "NF3040"

    @declarative.dproperty
    def ebridge(self, ebr):
        return ebr

    port = "/dev/ttyUSB1"

    def temp_controller_run(self, args):
        prg = tempController.TempControllerScript(
            ebridge=self.ebridge,
            port=self.port,
        )
        prg.main()

    @declarative.dproperty
    def process(self):
        return processes.SubscriptRunner(
            parent=self,
            ebridge=self.ebridge.process,
            script_name=self.script_name,
            run_function=self.temp_controller_run,
            # tee_script_output = True,
        )

    @declarative.mproperty
    def medm_full_panel(self):
        medm = epics_panels.VHNestedMEDM(
            [
                self.process.medm_panel,
                self.ebridge.medm_panel,
            ]
        )
        medm.medm_screen_filename_from_namechain(
            self.ebridge.egroup.name_chain.child("FPANEL")
        )
        return medm
