"""
"""
from __future__ import division, print_function, unicode_literals

import os
import sys
import declarative
import declarative.argparse as declarg
from declarative.utilities.future_from_2 import unicode
import collections
import socket

from . import cas9core

from ..config import pytoml

def config_dumps(dddict):
    return pytoml.dumps(dddict)

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
    def ctree_pull(self, val = False):
        """
        Specify as True to cause some copying in ctree to determine exactly all of the config values pulled from the configuration
        """
        return val

    @declarative.dproperty
    def root(self):
        root = cas9core.InstaCAS(
            prefix_base      = self.cmd.ifo,
            prefix_subsystem = self.cmd.subsystem,
            module_name     = self.cmd.module_name,
            ctree            = self.cmd.ctree,
            _ctree_pulling   = self.ctree_pull,
        )
        return root

    @declarative.dproperty
    def reloader(self):
        if self.cmd.auto_restart:
            from cas9epics.subservices.restart_on_edit import RestartOnEdit
            reloader = RestartOnEdit(
                name = 'reloader',
                parent = self.root,
            )
            return reloader
        return None

    @declarative.dproperty
    def task(self):
        return self.cmd.t_task(
            name = 'task',
            prefix = None,
            parent = self.root,
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
    def ctree(self):
        if self.config_file is not None:
            with open(self.config_file, 'r') as F:
                conf_dict = pytoml.load(F)
            return declarative.bunch.DeepBunchSingleAssign(conf_dict)
        else:
            return declarative.bunch.DeepBunchSingleAssign()

    @declarative.dproperty
    def _ctree_about(self):
        """
        Additional dictionary to store configuration docstrings for this "pre-root" command line setup. The config commands to display these documentation will merge this with the
        about dict in the root.ctree.
        """
        return declarative.bunch.DeepBunchSingleAssign()

    @declarg.argument(['-S, --site'])
    @declarative.dproperty
    def site(self, val = None):
        """
        Instrument site. Uses $SITE if not specified
        """
        config_val = self.ctree.get('site', None)
        if val is None:
            if config_val is None:
                val = os.getenv('SITE')
                self.ctree['SITE'] = val
            else:
                val = config_val
        if val is None:
            raise RuntimeError("SITE environment variable not set and not specified in config or on command line")
        self._ctree_about['SITE'] = (
            "Instrument site. Uses the command line --site parameter"
            " or defaults to $SITE if not specified. Precedence of configurations"
            " is 1. --site, 2. configfile.SITE 3. $SITE."
        )
        return val.lower()

    @declarg.argument(['-i, --ifo'])
    @declarative.dproperty
    def ifo(self, val = None):
        """
        Interferometer Prefix. Uses $IFO if not specified
        """
        config_val = self.ctree.get('IFO', val)
        if val is None:
            if config_val is None:
                val = os.getenv('IFO')
                self.ctree['IFO'] = val
            else:
                val = config_val
        if val is None:
            raise RuntimeError("IFO environment variable not set and not specified in config or on command line")
        self._ctree_about['IFO'] = (
            "Instrument (interferometer) prefix name. Uses the command line --ifo parameter"
            " or defaults to $IFO if not specified. Precedence of configurations"
            " is 1. --ifo, 2. configfile.IFO 3. $IFO."
        )
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
            config_val = 'test'
        else:
            config_val = val
        config_val = self.ctree.setdefault('subsystem_prefix', config_val)
        if val is None:
            val = config_val
        self._ctree_about['IFO'] = (
            "Subsystem prefix name. Used for naming channels with the (default pattern) X1:PREFIX-XXX_YYY_ZZZ."
            " Uses the command line --subsystem parameter"
            " Precedence of configurations is 1. --subsystem, 2. configfile.subsystem_prefix"
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
        val = self.ctree.setdefault('module_name_base', val)
        self._ctree_about['module_name_base'] = (
            "base name to create the program name from using module_name_template. One can alternately"
            " directly specify the program name if it does not depend on site, ifo, or other variables."
        )
        return val

    @declarative.dproperty
    def module_name_template(self, val = None):
        if val is None:
            val = '{ifo}{subsys}{base}'
        val = self.ctree.setdefault('module_name_template', val)
        self._ctree_about['module_name_base'] = (
            "Template to use to create the program name from"
            " directly specify the program name if it does not depend on site, ifo, or other variables."
            " May use variables {ifo}, {site}, {subsys}, {base}, {host} in the template."
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

    @declarg.command()
    def listPVs(self, argv):
        """
        List the CAS PVs hosted by this task
        """
        program = self.meta_program_generate()
        cas_db = program.root.cas_db_generate()
        pvs = list(cas_db.keys())
        pvs.sort()
        for pv in pvs:
            print(pv)

    @declarg.command()
    def config_print(self, argv):
        """
        Print the used configuration (takes subcommand arguments)
        """
        args = ConfigPrintArgs.__cls_argparse__(argv, no_commands = True)
        if args.about:
            ctree_pull = False
        elif args.check_unused or args.check_remaining:
            ctree_pull = True
        else:
            ctree_pull = False

        program = self.meta_program_generate(
            ctree_pull = ctree_pull,
        )

        db = declarative.DeepBunch()
        if not (args.epics_include or args.check_unused):
            db.update_recursive(program.root.ctree.extractidx('config'))

        if args.epics_include or args.check_unused:
            db.update_recursive(program.root.ctree.extractidx('epics'))

        if args.prefix_include or args.check_unused:
            db.update_recursive(program.root.ctree.extractidx('names'))

        db.update_recursive(program.root.ctree.extractidx('current'))
        db = remap_recursive(db.mydict)

        if args.about:
            def remap(val):
                if val == program.root.ctree.ABOUT_KEY:
                    return 'about'
                return val
            dabout = remap_recursive(program.root.ctree._abdict.mydict, remap)
            dabout_keep = declarative.DeepBunch()
            dict_kinclude(dabout, db, dabout_keep)

            dict_about_merge(dabout_keep, remap_recursive(self._ctree_about))

            print(config_dumps(dabout_keep.mydict))
            return

        if args.check_unused:
            dunused, d1diff, d2diff = dict_diff(self.ctree.mydict, db)
            print("#Unused:")
            print(config_dumps(dunused))
            if d2diff is not None:
                print("#diff in used:")
                print(config_dumps(d2diff))
            if d1diff is not None:
                print("#diff in config:")
                print(config_dumps(d1diff))
        elif args.check_remaining:
            dunused, d1diff, d2diff = dict_diff(db, self.ctree)
            print("#Remaining:")
            print(config_dumps(dunused))
            if d2diff is not None:
                print("#diff in config:")
                print(config_dumps(d2diff))
            if d1diff is not None:
                print("#diff in used:")
                print(config_dumps(d1diff))
        else:
            print(config_dumps(db))

class ConfigPrintArgs(
    declarg.OOArgParse,
    declarative.OverridableObject
):

    @declarg.store_true(['-A, --about'])
    @declarative.dproperty
    def about(self, val = False):
        """
        Print help annotated for all of the settings in the table.
        """
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

    @declarg.store_true(['-U, --check-unused'])
    @declarative.dproperty
    def check_unused(self, val = False):
        """
        List all configuration values in the configuration file which are not read during loading. (This changes the mode of the output). Not compatible with --check-remaining
        """
        return val

    @declarg.store_true(['-R, --check-remaining'])
    @declarative.dproperty
    def check_remaining(self, val = False):
        """
        List all of the settings which have not be fully set by the configuration value. This helps to lock down the configuration as program defaults may change. Not compatible with --check-unused.
        """
        if val and self.check_unused:
            print("Error Cannot set both --check-remaining and --check-unused", file = sys.stderr)
            sys.exit(-1)
        return val


def remap_recursive(d, remap = None):
    if remap is not None:
        d = remap(d)
    if isinstance(d, collections.Mapping):
        d2 = dict()
        for k, v in d.items():
            d2[remap_recursive(k, remap)] = remap_recursive(v, remap)
        return d2
    elif isinstance(d, (list, tuple)):
        d2 = []
        for v in d:
            d2.append(remap_recursive(v, remap))
        return d2
    elif isinstance(d, (int, float)):
        return d
    elif isinstance(d, (str, unicode)):
        return str(d)
    elif d is None:
        return d
    else:
        raise TypeError("Unknown Config Export type: {0}".format(repr(d)))


def dict_diff(d1, d2):
    d_unused = declarative.DeepBunch()
    d1_diff = declarative.DeepBunch()
    d2_diff = declarative.DeepBunch()
    _dict_diff(d1, d2, d_unused, d1_diff, d2_diff, None)
    d1_diff = d1_diff.mydict.get(None, None)
    d2_diff = d2_diff.mydict.get(None, None)
    return d_unused.mydict, d1_diff, d2_diff

def _dict_diff(d1, d2, d_unused, d1_diff, d2_diff, k_prev):
    """
    determines d1 - d2 in the set-subtraction sense. Separates d_unused and d1_diff and d2_diff
    """
    if isinstance(d1, collections.Mapping):
        if not isinstance(d2, collections.Mapping):
            d1_diff[k_prev] = d1
            d2_diff[k_prev] = d2

        for k, v in d1.items():
            if k not in d2:
                d_unused[k] = v
            else:
                _dict_diff(d1[k], d2[k], d_unused[k], d1_diff[k_prev], d2_diff[k_prev], k_prev = k)
    else:
        if d1 != d2:
            d1_diff[k_prev] = d1
            d2_diff[k_prev] = d2


def dict_kinclude(d1, d2, d_keep):
    """
    Keep only keys of d1 that are in d2
    """
    if isinstance(d1, collections.Mapping):
        if not isinstance(d2, collections.Mapping):
            return True

        for k, v in d1.items():
            if k not in d2:
                return False
            else:
                if dict_kinclude(d1[k], d2[k], d_keep[k]):
                    d_keep[k] = d1[k]
        return False
    else:
        return False


def dict_about_merge(d1, d2):
    """
    Merges d2 into d1, adds "about" keys which are missing from d2. Intended to merge the CAS9CmdLine._ctree_about with the root.ctree.about dictionary
    """
    if not isinstance(d2, collections.Mapping):
        #TODO, avoid this cast
        #have to cast to str to avoid unicode typing that annoys YAML
        d1[str('about')] = d2
    else:
        for k, v in d2.items():
            dict_about_merge(d1[k], v)


class CAS9Module(cas9core.CASUser):
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
