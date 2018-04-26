"""
"""
from __future__ import division, print_function, unicode_literals

import declarative
from declarative import bunch

from . import reactor
from . import pcaspy_backend
from . import cas9declarative


class InstaCAS(
    pcaspy_backend.CASCollector,
    declarative.OverridableObject
):

    @cas9declarative.dproperty
    def reactor(self):
        return reactor.Reactor()

    @cas9declarative.dproperty
    def autosave(self):
        from ..subservices import autosave
        return autosave.AutoSave(
            parent = self,
            name = 'burt',
        )

    @cas9declarative.dproperty
    def prefix_base(self, val = None):
        if val is None:
            val = 'X1'
        return val

    @cas9declarative.dproperty
    def prefix_subsystem(self, val = None):
        if val is None:
            val = 'TEST'
        return val

    @cas9declarative.dproperty_ctree(default = None)
    def module_name(self, val):
        if val is None:
            val = '{0}{1}unnamed'.format(self.prefix_base, self.prefix_subsystem).lower()
        return val

    @cas9declarative.dproperty
    def prefix_full(self):
        if self.prefix_subsystem is None:
            val = ()
        else:
            val = (self.prefix_subsystem,)
        return val

    def prefix2channel(self, prefix):
        chn = '{0}:{1}-'.format(self.prefix_base, prefix[0]) + '_'.join(prefix[1:])
        chn = chn.upper()
        return chn

    def start(self):
        if self._db_generated is None:
            self._db_generated = self.cas_db_generate()
            self._cas_generated = pcaspy_backend.CADriverServer(
                self._db_generated,
                self.reactor,
                saver = self.autosave,
            )
            self._cas_generated.start()
            return True
        return False

    _db_generated = None
    _cas_generated = None
    def run(self, for_s = None, modulo_s = None, mtime_to = None):
        #TODO decide if arguments should change how stopping is done on errors
        self.start()

        if for_s is None and modulo_s is None and mtime_to is None:
            try:
                self.reactor.run_reactor()
            finally:
                self.stop()
        else:
            self.reactor.flush(
                for_s    = for_s,
                modulo_s = modulo_s,
                mtime_to = mtime_to,
            )
        return

    def stop(self):
        if self._db_generated is not None:
            self._cas_generated.stop()
            self._db_generated = None
            self._cas_generated = None

    @cas9declarative.dproperty
    def root(self):
        return self

    @cas9declarative.mproperty
    def ctree(self, arg = cas9declarative.NOARG):
        about   = bunch.DeepBunchSingleAssign()
        current = bunch.DeepBunchSingleAssign()
        names   = bunch.DeepBunchSingleAssign()
        epics   = bunch.DeepBunchSingleAssign()
        dicts = [current, names, epics]

        #add in the configuration argument one as the last (it is never assigned into)
        if arg is not cas9declarative.NOARG:
            dicts.append(arg)

        if not self._ctree_pulling:
            return cas9declarative.ShadowBunchN(dicts, abdict = about)
        else:
            return cas9declarative.ShadowBunchNPull(dicts, abdict = about)

    #indicate that the configs should also be pulled. Useful for some ctree inspections
    _ctree_pulling = False


class CASUser(declarative.OverridableObject):
    name_default = None

    @cas9declarative.dproperty
    def parent(self, val):
        return val

    @cas9declarative.dproperty
    def name(self, val = None):
        if val is None:
            val = self.name_default
        if val is None:
            raise RuntimeError("Must specify object name")
        return val

    @cas9declarative.dproperty
    def prefix(self, val = cas9declarative.NOARG):
        if val is cas9declarative.NOARG:
            val = self.name
        return val

    @cas9declarative.dproperty
    def prefix_full(self):
        if self.prefix is None:
            default = tuple(self.parent.prefix_full)
        else:
            default = tuple(self.parent.prefix_full) + (self.prefix,)
        val = self.ctree.useidx('names').setdefault(
            'prefix',
            default,
            about = ("""
                configtype : nested_prefix
                List of strings which chain to construct channel names of child objects.
                If parent prefixes are changed, then child prefixes will change unless
                they are also specified in the configuration
            """)
        )
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

    def cas_host(self, rv, name = None, **kwargs):
        return self.root.cas_host(
            rv     = rv,
            name   = name,
            prefix = self.prefix_full,
            ctree  = self.ctree['PVs'].useidx('epics'),
            **kwargs
        )

