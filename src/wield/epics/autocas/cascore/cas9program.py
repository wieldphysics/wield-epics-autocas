#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2021 Massachusetts Institute of Technology.
# SPDX-FileCopyrightText: © 2021 Lee McCuller <mcculler@caltech.edu>
# NOTICE: authors should document their contributions in concisely in NOTICE
# with details inline in source files, comments, and docstrings.
"""
"""


import os
import sys
import socket

from wield import declarative
from wield.declarative import argparse as declarg

from ..config import pytoml

from . import cascore
from . import ctree
from . import program


class CAS9MetaProgram(
    declarative.OverridableObject
):
    """
    Takes a CAS9CmdLine and creates a root and related objects from it.
    It cannot be put directly in CAS9CmdLine so that the program can add some advanced settings.
    """
    @declarative.dproperty
    def cmd(self, val):
        return val

    @declarative.dproperty
    def root(self):
        root = cascore.InstaCAS(
            prefix_base      = self.cmd.ifo,
            prefix_subsystem = self.cmd.subsystem,
            module_name      = self.cmd.module_name,
            ctree_root       = self.cmd.ctree_root,
            config_files     = [
                self.cmd.config_file,
            ],
        )
        return root

    @declarative.dproperty
    def reloader(self):
        if self.cmd.auto_restart:
            from wield.epics.autocas.subservices.restart_on_edit import RestartOnEdit
            reloader = RestartOnEdit(
                name = 'reloader',
                parent = self.root,
            )
            return reloader
        return None

    @declarative.dproperty
    def task(self):
        return self.cmd.t_task(
            name      = 'task',
            subprefix = None,
            parent    = self.root,
        )


class CAS9CmdLine(
    declarg.OOArgParse,
    declarative.OverridableObject
):
    """
    Command line interface to boot up an InstaCAS object and associated task. Cannot use some features such as dproperty_ctree since those are designed for CASUser or InstaCAS objects.
    """

    @declarg.argument(['-c, --config'], metavar = 'fname')
    @declarative.dproperty
    def config_file(self, val = None):
        """
        Configuration File
        """
        if val is None:
            print("Warning: No Configuration File Specified, using defaults", file = sys.stderr)
        return val

    @declarative.dproperty
    def ctree_root(self):
        ctree_root = ctree.ConfigTreeRoot()
        if self.config_file is not None:
            with open(self.config_file, 'r') as F:
                conf_dict = pytoml.load(F)
            ctree_root.config_load_recursive(conf_dict)
        return ctree_root

    @declarative.dproperty
    def ctree(self):
        return self.ctree_root.ctree

    @declarg.argument(['-S, --site'])
    @declarative.dproperty
    def site(self, val = None):
        """
        Instrument site. Uses $SITE if not specified
        """

        if val is None:
            default = os.getenv('SITE')
            val = self.ctree.get_configured(
                'SITE',
                default = default,
                about = (
                    "Instrument site. Uses the command line --site parameter"
                    " or defaults to $SITE if not specified. Precedence of configurations"
                    " is 1. --site, 2. configfile.SITE 3. $SITE."
                )
            )
        if val is None:
            raise RuntimeError("SITE environment variable not set and not specified in config or on command line")
        return val.lower()

    @declarg.argument(['-i, --ifo'])
    @declarative.dproperty
    def ifo(self, val = None):
        """
        Interferometer Prefix. Uses $IFO if not specified
        """
        if val is None:
            default = os.getenv('IFO')
            val = self.ctree.get_configured(
                'IFO',
                default = default,
                about = (
                    "Instrument (interferometer) prefix name. Uses the command line --ifo parameter"
                    " or defaults to $IFO if not specified. Precedence of configurations"
                    " is 1. --ifo, 2. configfile.IFO 3. $IFO."
                )
            )
        if val is None:
            raise RuntimeError("IFO environment variable not set and not specified in config or on command line")
        return val.lower()

    #can also override this in subclasses
    @declarg.argument(['-s, --subsystem'], metavar = 'name')
    @declarative.dproperty
    def subsystem(self, val = None):
        """
        Subsystem prefix for channel names using the (default) format
        X1:PREFIX-XXX_YYY_ZZZ
        """
        if val is None:
            default = 'test'
        else:
            default = val
        val = self.ctree.get_configured(
            'subsystem_prefix',
            default = default,
            about = (
                "Subsystem prefix name. Used for naming channels with the (default pattern) X1:PREFIX-XXX_YYY_ZZZ."
                " Uses the command line --subsystem parameter"
                " Precedence of configurations is 1. --subsystem, 2. configfile.subsystem_prefix"
            )
        )
        return val

    @declarg.store_true(['-R, --auto-restart'])
    @declarative.dproperty
    def auto_restart(self, val = None):
        """
        Use the filesystem watch and automatic restart tool (good for development)
        """
        if val is None:
            val = False
        return val

    #must specify in base classes or as a default
    @declarative.dproperty
    def t_task(self, val = None):
        if val is None:
            raise NotImplementedError("Subclasses must specify t_task as the system to start running")
        return val

    @declarative.dproperty
    def module_name_base(self, val = None):
        """
        Subsystem prefix for channel names using the (default) format
        X1:PREFIX-XXX_YYY_ZZZ
        """
        if val is None:
            val = self.t_task.__name__.lower()
        val = self.ctree.get_configured(
            'module_name_base',
            default = val,
            about = (
                "base name to create the program name from using module_name_template. One can alternately"
                " directly specify the program name if it does not depend on site, ifo, or other variables."
            ),
        )
        return val

    @declarative.dproperty
    def module_name_template(self, val = None):
        if val is None:
            val = '{ifo}{subsys}{base}'
        val = self.ctree.get_configured(
            'module_name_template',
            val,
            about = (
                "Template to use to create the program name from"
                " directly specify the program name if it does not depend on site, ifo, or other variables."
                " May use variables {ifo}, {site}, {subsys}, {base}, {host} in the template."
            )
        )
        return val

    @declarg.argument(
        ['-H, --hostname'],
        default = lambda : socket.gethostname().split('.')[0],
        metavar = 'name'
    )
    @declarative.dproperty
    def hostname(self, val = None):
        """
        Hostname variable used for naming templates. Defaults to the hostname before all dots in the system domain name: \"{default}\".
        """
        return val

    @declarative.dproperty
    def module_name(self):
        """
        The InstaCAS root object stores the configuration, this just computes the default value.
        """
        template = self.module_name_template
        val = template.format(
            ifo    = self.ifo,
            site   = self.site,
            subsys = self.subsystem,
            base   = self.module_name_base,
            host   = self.hostname,
        )
        return val

    t_meta_program = CAS9MetaProgram

    def meta_program_generate(self, **kwargs):
        return self.t_meta_program(
            cmd = self,
            **kwargs
        )

    @declarg.command()
    def run(self, args):
        """
        Main method to start running the task
        """
        program = self.meta_program_generate()
        try:
            program.root.run()
        except KeyboardInterrupt:
            print('KeyboardInterrupt', file = sys.stderr)

    @declarg.command(takes_arguments = True)
    def list(self, argv):
        """
        List PVs and other resources used in this application
        """
        #TODO, make this a nicer hack for the usage_prog
        idx = sys.argv.index(self.__cls_argparse_cmd__)

        return program.list.ListArgs.__cls_argparse__(
            argv,
            cmd = self,
            __usage_prog__ = (' '.join(sys.argv[:idx + 1])),
        )

    @declarg.command(takes_arguments = True)
    def config(self, argv):
        """
        Print the used configuration (takes subcommand arguments)
        """
        #TODO, make this a nicer hack for the usage_prog
        idx = sys.argv.index(self.__cls_argparse_cmd__)

        return program.config.ConfigArgs.__cls_argparse__(
            argv,
            cmd = self,
            __usage_prog__ = (' '.join(sys.argv[:idx + 1])),
        )


class CAS9Module(cascore.CASUser):
    t_cas9cmdline = CAS9CmdLine

    @classmethod
    def cmdline(
        cls,
        args = None,
        module_name_base = None,
        t_cas9cmdline = None,
        **kwargs
    ):
        if t_cas9cmdline is None:
            t_cas9cmdline = cls.t_cas9cmdline

        return t_cas9cmdline.__cls_argparse__(
            args,
            t_task = cls,
            module_name_base = module_name_base,
            **kwargs
        )
