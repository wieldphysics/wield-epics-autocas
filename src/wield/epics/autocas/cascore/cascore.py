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

from . import reactor
from . import pcaspy_backend
from . import pyepics_backend
from . import base_backend
from . import cas9declarative
from . import ctree


class InstaCAS(base_backend.CASCollector, declarative.OverridableObject):
    @cas9declarative.dproperty
    def reactor(self):
        return reactor.Reactor()

    @cas9declarative.dproperty
    def autosave(self):
        from ..subservices import autosave

        return autosave.AutoSave(
            parent=self,
            name="burt",
        )

    @cas9declarative.dproperty
    def settings(self):
        from ..subservices import program_status

        return program_status.ProgramSettings(
            parent=self,
            name="settings",
        )

    @cas9declarative.dproperty
    def status(self, val=declarative.NOARG):
        if val is declarative.NOARG:
            from ..subservices import program_status

            return program_status.ProgramStatus(
                parent=self,
                name="status",
                prefix=self.prefix + (self.module_name, "status"),
            )
        return val

    @cas9declarative.dproperty
    def prefix_base(self, val=None):
        if val is None:
            val = "X1"
        return val

    @cas9declarative.dproperty
    def prefix_subsystem(self, val=None):
        if val is None:
            val = "TEST"
        return val

    @cas9declarative.dproperty_ctree(default=None)
    def module_name(self, val):
        if val is None:
            val = "{0}{1}unnamed".format(
                self.prefix_base, self.prefix_subsystem
            ).lower()
        return val

    @cas9declarative.dproperty
    def prefix(self):
        if self.prefix_subsystem is None:
            val = ()
        else:
            val = (self.prefix_subsystem,)
        return val

    def prefix2channel(self, prefix):
        chn = "{0}:{1}-".format(self.prefix_base, prefix[0]) + "_".join(prefix[1:])
        chn = chn.upper()
        return chn

    def start(self):
        if self._db_generated is None:
            self._db_generated = self.cas_db_generate()
            self._cas_generated = pcaspy_backend.CADriverServer(
                self._db_generated,
                self.reactor,
                saver=self.autosave,
            )
            self._cas_remote = pyepics_backend.CAEpicsClient(
                self._db_generated,
                self.reactor,
                saver=self.autosave,
            )
            self._cas_generated.start()
            self._cas_remote.start()
            return True
        return False

    _db_generated = None
    _cas_generated = None
    _cas_remote = None

    def run(self, for_s=None, modulo_s=None, mtime_to=None):
        # TODO decide if arguments should change how stopping is done on errors
        self.start()

        if for_s is None and modulo_s is None and mtime_to is None:
            try:
                self.reactor.run_reactor()
            finally:
                self.stop()
        else:
            self.reactor.flush(
                for_s=for_s,
                modulo_s=modulo_s,
                mtime_to=mtime_to,
            )
        return

    def stop(self):
        if self._db_generated is not None:
            self._cas_generated.stop()
            self._cas_remote.stop()
            self._db_generated = None
            self._cas_generated = None

    @cas9declarative.dproperty
    def config_files(self, val=None):
        """
        additional list of configurations for the system to be aware of
        """
        if val is None:
            val = []
        else:
            val = list(val)
        return val

    @cas9declarative.dproperty
    def root(self):
        return self

    @cas9declarative.dproperty
    def ctree_root(self, arg=cas9declarative.NOARG):
        # the configtree may be specified externally but it should be
        # a ConfigTreeRoot or compatible type
        if arg is cas9declarative.NOARG:
            arg = ctree.ConfigTreeRoot()
        return arg

    @cas9declarative.mproperty
    def ctree(self, arg=cas9declarative.NOARG):
        return self.ctree_root.ctree


class CASUser(declarative.OverridableObject):
    name_default = None

    @cas9declarative.dproperty
    def parent(self, val):
        return val

    @cas9declarative.dproperty
    def name(self, val=None):
        if val is None:
            val = self.name_default
        if val is None:
            raise RuntimeError("Must specify object name")
        return val

    @cas9declarative.dproperty
    def subprefix(self, val=cas9declarative.NOARG):
        if val is cas9declarative.NOARG:
            val = (self.name,)
        elif val is None:
            val = ()
        else:
            if isinstance(val, str):
                val = (val,)
            else:
                val = tuple(val)
        return val

    @cas9declarative.dproperty
    def prefix(self, val=cas9declarative.NOARG):
        if val is cas9declarative.NOARG:
            default = tuple(self.parent.prefix) + self.subprefix

            val = self.ctree.get_configured(
                "prefix",
                default=default,
                about=(
                    "List of strings which chain to construct channel names of child objects."
                    " If parent prefixes are changed, then child prefixes will change unless"
                    " they are also specified in the configuration."
                ),
                classification="prefix",
            )

        assert isinstance(val, (list, tuple))
        for p in val:
            assert isinstance(p, str)
            assert "." not in p
        val = tuple(val)
        return val

    @cas9declarative.dproperty
    def root(self):
        return self.parent.root

    @cas9declarative.mproperty
    def reactor(self):
        return self.root.reactor

    @cas9declarative.mproperty
    def ctree(self):
        return self.parent.ctree[self.name]

    def cas_host(self, rv, name=None, **kwargs):
        return self.root.cas_host(
            rv=rv, name=name, self_prefix=self.prefix, ctree=self.ctree["PVs"], **kwargs
        )
