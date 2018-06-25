"""
"""
from __future__ import division, print_function, unicode_literals

from .. import cas9core
from . import cas_time

def time_validator(val):
    assert(val in ['UNIX', 'GPS'])
    return val

class ProgramSettings(cas9core.CASUser):
    @cas9core.dproperty_ctree(default = 'GPS', validator = time_validator)
    def time_convention(self, val):
        return val


class ProgramStatus(cas9core.CASUser):
    """
    Service class which hosts variables related to the status of standard subcomponents of a CAS System. This includes

    reactor latency
    reactor queue depth
    last reactor fault

    last burt time

    number of missing remote PVs, with names for first 5 missing.
    number of hosted PVs
    hostname
    version
    software-hash
    config-hash
    cpu usage of program (maybe).

    global error status
    """

    @cas9core.dproperty
    def rv_reactor_latency_ms(self):
        rv = cas9core.RelayValueFloat(-1)
        self.cas_host(
            rv, 'REACTOR_LAT_MS',
            unit  = 'milliseconds',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_reactor_fill(self):
        rv = cas9core.RelayValueInt(-1)
        self.cas_host(
            rv, 'REACTOR_FILL',
            unit  = 'number',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_reactor_canary(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'REACTOR_FAULT_TIME',
            unit  = 'datetime',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_PVs_missing(self):
        rv = cas9core.RelayValueInt(0)
        self.cas_host(
            rv, 'PVS_MISSING',
            unit  = 'number',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_PVs_hosted(self):
        rv = cas9core.RelayValueInt(0)
        self.cas_host(
            rv, 'PVS_HOSTED',
            unit  = 'number',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_about_hostname(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'HOSTNAME',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_about_version(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'VERSION',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_about_cpu(self):
        rv = cas9core.RelayValueFloat(-1)
        self.cas_host(
            rv, 'CPU_USAGE',
            unit  = 'percentage',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_about_softhash(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'ABOUT_SOFTHASH',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_about_confhash(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'ABOUT_CONFHASH',
            interaction = 'report',
        )
        return rv

    @cas9core.dproperty
    def rv_burt_time(self):
        rv = cas9core.RelayValueString('<TODO>')
        self.cas_host(
            rv, 'BURT_TIME',
            unit  = 'datetime',
            interaction = 'report',
        )
        return rv

