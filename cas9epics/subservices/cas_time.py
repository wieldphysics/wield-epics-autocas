"""
"""
from __future__ import division, print_function, unicode_literals

import time
import datetime

from .. import cas9core

class DateTime(cas9core.CASUser):
    @cas9core.dproperty
    def rv_str(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'STR',
            unit  = 'datetime',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_float(self, default = 0):
        rv = cas9core.RelayValueFloat(default)
        self.cas_host(
            rv, 'ORD',
            unit  = self.root.settings.time_convention,
            interaction = 'report',
        )
        return rv

    def update_unix_time(self, unix_time):
        if self.root.settings.time_convention == 'UNIX':
            self.rv_float.value = unix_time
        elif self.root.settings.time_convention == 'GPS':
            #LIGO library
            import gpstime
            self.rv_float.value = gpstime.unix2gps(unix_time)
        dt = datetime.datetime.fromtimestamp(unix_time)
        self.rv_str.value = dt.strptime('%X %x')

    def update_now(self):
        self.update_unix_time(time.time())

