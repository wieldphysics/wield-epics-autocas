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
from wield.declarative import argparse as declarg


class ListArgs(
    declarg.OOArgParse,
    declarative.OverridableObject
):
    @declarative.dproperty
    def cmd(self, val):
        return val

    @declarg.command()
    def hostedPVs(self, argv):
        """
        List the CAS PVs hosted by this task
        """
        program = self.cmd.meta_program_generate()
        #TODO, make this not list external
        cas_db = program.root.cas_db_generate()
        pvs = list(cas_db.keys())
        pvs.sort()
        for pv in pvs:
            if not cas_db[pv]['remote']:
                print(pv)

    @declarg.command()
    def remotePVs(self, argv):
        """
        List the external PVs connected by this task
        """
        program = self.cmd.meta_program_generate()
        #TODO, make this not list external
        cas_db = program.root.cas_db_generate()
        pvs = list(cas_db.keys())
        pvs.sort()
        for pv in pvs:
            if cas_db[pv]['remote']:
                print(pv)



