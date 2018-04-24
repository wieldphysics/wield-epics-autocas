"""
"""
from __future__ import division, print_function, unicode_literals

import declarative
import contextlib

from . import cas9core


class RVError(cas9core.CASUser):
    name_default = 'ERR'

    @declarative.dproperty
    def rv_str(self):
        rv = cas9core.RelayValueString('')
        self.cas_host(
            rv, 'STR',
            unit  = 'message',
            writable = False,
        )
        return rv

    @declarative.dproperty
    def rv_level(self):
        rv = cas9core.RelayValueInt(0)
        self.cas_host(
            rv, 'LEVEL',
            unit  = 'level',
            writable = False,
        )
        return rv

    @declarative.dproperty
    def rv_thresh(self):
        rv = cas9core.RelayValueInt(10)
        self.cas_host(
            rv, 'THR',
            unit  = 'level',
            writable = False,
        )
        return rv

    _holding = False
    _level_temp = None
    _str_temp = None

    def __call__(self, level, msg):
        if self._holding:
            if self._level_temp is None or level < self._level_temp:
                self._level_temp = level
                self._str_temp   = msg
            #do nothing if level is not superceded
        else:
            if level < self.rv_level.value:
                self.rv_level.value = level
                self.rv_str.value   = msg

    def clear(self):
        self.rv_str.value = ''
        self.rv_level.value = self.rv_thresh.value
        return

    @contextlib.contextmanager
    def clear_pending(self):
        if self._holding:
            yield
        else:
            self._holding = True
            self._level_temp = None
            self._str_temp = None
            yield
            if self._level_temp is None or self._level_temp >= self.rv_thresh.value:
                self.rv_str.value = ''
                self.rv_level.value = self.rv_thresh.value
            else:
                self.rv_str.value = self._str_temp
                self.rv_level.value = self._level_temp
            del self._holding
