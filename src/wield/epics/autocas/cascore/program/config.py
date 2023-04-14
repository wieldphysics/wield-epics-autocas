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

from ...config import nested_dict_utils
from ...config import pytoml


def config_dumps(dddict):
    return pytoml.dumps(dddict)


class ConfigArgs(
    declarg.OOArgParse,
    declarative.OverridableObject
):
    @declarative.dproperty
    def cmd(self, val):
        return val

    @declarg.store_true(['-E, --epics'])
    @declarative.dproperty
    def epics_include(self, val = False):
        """
        Include all of the registered epics variables and settings. This is very verbose, but can provide tunable settings such as limit and alarm values.
        """
        return val

    @declarg.store_true(['-P, --prefix'])
    @declarative.dproperty
    def prefix_include(self, val = False):
        """
        Include all of the device prefix names. This allows one to change the prefix listing used to generate epics variable names by adjusting high levels of the hierarchy.
        """
        return val

    def __arg_default__(self):
        """
        Print the configuration as used, including all defaults. Hides defaults for epics PVs as there are many.
        """
        #TODO add these back in
        #if args.about:
        #    ctree_pull = False
        #elif args.check_unused or args.check_remaining:
        #    ctree_pull = True
        #else:
        #    ctree_pull = False

        program = self.cmd.meta_program_generate()

        db = DeepBunch()
        db.update_recursive(program.root.ctree_root.value_retrieve_recursive())
        db = nested_dict_utils.remap_recursive(db.mydict)

        print(config_dumps(db))

    @declarg.command()
    def remaining(self, argv):
        """
        List all of the settings which have not be fully set by the configuration value. This helps to lock down the configuration as program defaults may change. Not compatible with --check-unused.
        """
        raise NotImplementedError("Need to implement the remaining printer")
        return

    @declarg.command()
    def unused(self, argv):
        """
        List all configuration values in the configuration file which are not read during loading.
        """
        raise NotImplementedError("Need to implement the unused printer")
        return

    @declarg.command()
    def about(self, argv):
        """
        Print help annotated for all of the settings in the table.
        """
        raise NotImplementedError("Need to implement the about printer")
        return




