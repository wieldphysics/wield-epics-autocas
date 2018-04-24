"""
"""
from __future__ import division, print_function, unicode_literals

import declarative
from declarative import bunch

from . import reactor
from . import pcaspy_backend
#from . import relay_values


class ShadowBunchN(bunch.ShadowBunch):
    _names = {
        'current'  :  0,
        'names'    :  1,
        'epics'    :  2,
        'config'   :  3,
    }

class ShadowBunchNPull(ShadowBunchN):
    """
    ShadownBunch for ctree that also stores every access to determine what was stored. For diffs and config pruning
    """
    _pull_full = True

class InstaCAS(
        pcaspy_backend.CASCollector,
        declarative.OverridableObject
):

    @declarative.dproperty
    def reactor(self):
        return reactor.Reactor()

    @declarative.dproperty
    def prefix_base(self, val = None):
        if val is None:
            val = 'X1'
        return val

    @declarative.dproperty
    def prefix_subsystem(self, val = None):
        if val is None:
            val = 'TEST'
        return val

    @declarative.dproperty
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
            self._cas_generated = pcaspy_backend.CADriverServer(self._db_generated, self.reactor)
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

    @declarative.dproperty
    def root(self):
        return self

    @declarative.mproperty
    def ctree(self, arg = declarative.NOARG):
        about   = bunch.DeepBunchSingleAssign()
        current = bunch.DeepBunchSingleAssign()
        names   = bunch.DeepBunchSingleAssign()
        epics   = bunch.DeepBunchSingleAssign()
        dicts = [current, names, epics]

        #add in the configuration argument one as the last (it is never assigned into)
        if arg is not declarative.NOARG:
            dicts.append(arg)

        if not self._ctree_pulling:
            return ShadowBunchN(dicts, abdict = about)
        else:
            return ShadowBunchNPull(dicts, abdict = about)

    #indicate that the configs should also be pulled. Useful for some ctree inspections
    _ctree_pulling = False


class CASUser(declarative.OverridableObject):
    name_default = None

    @declarative.dproperty
    def parent(self, val):
        return val

    @declarative.dproperty
    def name(self, val = None):
        if val is None:
            val = self.name_default
        if val is None:
            raise RuntimeError("Must specify object name")
        return val

    @declarative.dproperty
    def prefix(self, val = declarative.NOARG):
        if val is declarative.NOARG:
            val = self.name
        return val

    @declarative.dproperty
    def prefix_full(self):
        if self.prefix is None:
            default = tuple(self.parent.prefix_full)
        else:
            default = tuple(self.parent.prefix_full) + (self.prefix,)
        val = self.ctree.useidx('names').setdefault('prefix', default)
        return val

    @declarative.dproperty
    def root(self):
        return self.parent.root

    @declarative.mproperty
    def reactor(self):
        return self.root.reactor

    @declarative.mproperty
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

dproperty = declarative.dproperty
mproperty = declarative.mproperty
__NOARG = declarative.utilities.unique_generator()

def dproperty_ctree(func = None, default = __NOARG):
    """
    automatically grabs the value from the ctree to pass along. The function should do the string conversion and validation
    """
    def deferred(func):
        if default is __NOARG:
            def superfunc(self, val):
                val = self.ctree.setdefault(
                    func.__name__, val,
                    about = func.__doc__,
                )
                return func(val)
        else:
            def superfunc(self, val = default):
                val = self.ctree.setdefault(
                    func.__name__, val,
                    about = func.__doc__,
                )
                return func(val)
        superfunc.__name__ = func.__name__
        superfunc.__doc__  = func.__doc__
        return declarative.dproperty(superfunc)
    if func is None:
        return deferred
    else:
        return deferred(func)

