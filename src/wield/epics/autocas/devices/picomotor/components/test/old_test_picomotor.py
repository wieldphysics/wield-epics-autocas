#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""
from os import path

_modpath, _modfile = path.split(__file__)

from YALL.utilities.name_chain import NameChain

from YALL.libholo.tools.scripting_system import ScriptLauncher
from YALL.libholo.fpga_bridge.picomotor.ebridges import (
    PicomotorConnectionMapping,
    PicomotorMapping,
)
from YALL.libholo.fpga_bridge.picomotor.medm_mappings import PicomotorMEDM
from YALL.libholo.fpga_bridge.picomotor.launcher import PicomotorSetLauncher


if __name__ == "__main__":
    launcher = ScriptLauncher(name_suffix="local", launch_folder="./test_launch_tmp")

    pico_nc = NameChain("local").child("picomotor")

    pico_connect_nc = pico_nc.child("connection")
    pico_connect_epics = PicomotorConnectionMapping(name_chain=pico_connect_nc)
    launcher.register_epics_pool(pico_connect_epics)

    pico_prm_nc = pico_nc.child("PRM")
    pico_prm_epics = PicomotorMapping(name_chain=pico_prm_nc)
    launcher.register_epics_pool(pico_prm_epics)

    pico_BS_nc = pico_nc.child("BS")
    pico_BS_epics = PicomotorMapping(name_chain=pico_BS_nc)
    launcher.register_epics_pool(pico_BS_epics)

    pico_peri_nc = pico_nc.child("periscope")
    pico_peri_epics = PicomotorMapping(name_chain=pico_peri_nc)
    launcher.register_epics_pool(pico_peri_epics)

    pico_prm_medm = PicomotorMEDM(pico_prm_epics, pico_connect_epics)
    launcher.register_medm_pool(pico_prm_medm)
    launcher.register_medm_main_view(pico_prm_medm)

    pico_BS_medm = PicomotorMEDM(pico_BS_epics, pico_connect_epics)
    launcher.register_medm_pool(pico_BS_medm)
    launcher.register_medm_main_view(pico_BS_medm)

    pico_peri_medm = PicomotorMEDM(pico_peri_epics, pico_connect_epics)
    launcher.register_medm_pool(pico_peri_medm)
    launcher.register_medm_main_view(pico_peri_medm)

    picomotor_launcher = PicomotorSetLauncher(
        pico_connect_epics, "mp8-picomotor.fnal.gov"  # , fake = True
    )
    picomotor_launcher.picomotor_add(pico_BS_epics, 1, 0, 1, 1)
    picomotor_launcher.picomotor_add(pico_prm_epics, 1, 2, 2, 0)
    picomotor_launcher.picomotor_add(pico_peri_epics, 2, 1, 2, 2)
    launcher.register_launcher_pool(picomotor_launcher)

    launcher.build_configurations()
    launcher.run(build=False)
