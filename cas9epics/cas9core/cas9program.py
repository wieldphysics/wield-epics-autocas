"""
"""
from __future__ import division, print_function, unicode_literals

import os
import sys
import declarative
import declarative.argparse as declarg
from declarative.utilities.future_from_2 import unicode
import yaml
import collections

from . import cas9core


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

    @declarg.argument(['-c, --config'])
    @declarative.dproperty
    def config_file(self, val = None):
        """
        Configuration File
        """
        if val is None:
            print("Warning: No Configuration File Specified, using defaults", file = sys.stderr)
        return val

    @declarg.store_true(['-j, --json-only'])
    @declarative.dproperty
    def json_use(self, val = False):
        """
        Use JSON to interpret configuration (no need to load yaml library)
        """
        if val:
            raise NotImplementedError("Not yet implemented")
        return val

    @declarative.dproperty
    def ctree(self):
        if self.config_file is not None:
            with open(self.config_file, 'r') as F:
                conf_dict = yaml.safe_load(F)
            return declarative.bunch.DeepBunchSingleAssign(conf_dict)
        else:
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
        return val.lower()

    #can also override this in subclasses
    @declarg.argument(['-s, --subsystem'])
    @declarative.dproperty
    def subsystem(self, val = None):
        """
        Subsystem prefix for channel names using the (default) format
        X1:PREFIX-XXX_YYY_ZZZ
        """
        if val is None:
            config_val = 'TEST'
        else:
            config_val = val
        config_val = self.ctree.setdefault('subsystem_prefix', config_val)
        if val is None:
            val = config_val
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

    #must specify in base classes
    def t_task(self):
        raise NotImplementedError("Subclasses must specify t_task as the system to start running")

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
            print(yaml.dump(dabout_keep.mydict))
            return

        if args.check_unused:
            dunused, d1diff, d2diff = dict_diff(self.ctree.mydict, db)
            print("#Unused:")
            print(yaml.dump(dunused))
            if d2diff is not None:
                print("#diff in used:")
                print(yaml.dump(d2diff))
            if d1diff is not None:
                print("#diff in config:")
                print(yaml.dump(d1diff))
        elif args.check_remaining:
            dunused, d1diff, d2diff = dict_diff(db, self.ctree)
            print("#Remaining:")
            print(yaml.dump(dunused))
            if d2diff is not None:
                print("#diff in config:")
                print(yaml.dump(d2diff))
            if d1diff is not None:
                print("#diff in used:")
                print(yaml.dump(d1diff))
        else:
            print(yaml.dump(db))

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




