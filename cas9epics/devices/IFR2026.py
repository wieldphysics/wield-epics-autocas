"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

import cas9core

from .. import relay_values
from .. import cas9core

#from . import utilities


class IFR2026Controls(
    cas9core.CASUser,
):
    @cas9core.dproperty
    def serial(self, val):
        return val

    @cas9core.dproperty
    def serial_id_check(self):
        def action_sequence(cmd):
            print("START BLOCK 2026")
            cmd.writeline('*IDN?')
            val = cmd.readline()
            #TODO PARSE
            print(val)
            #if this is NOT called, then serial calls it automatically
            try:
                cmd.block_remainder()
                print("DONE BLOCK 2026")
            finally:
                pass

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            name = 'id_check',
            prefix = self.prefix_full,
        )
        return block

    @cas9core.dproperty
    def chnA(self):
        return IFR2026Channel(
            parent = self,
            name = 'chnA',
            channel_name = 'A',
            prefix = 'CLF2',
        )

    @cas9core.dproperty
    def chnB(self):
        return IFR2026Channel(
            parent = self,
            name = 'chnB',
            prefix = 'ALF',
            channel_name = 'B',
        )


class IFR2026Channel(
    cas9core.CASUser,
):
    "Must be hosted by a IFR2026"

    @cas9core.dproperty
    def serial(self):
        return self.parent.serial

    @cas9core.dproperty
    def channel_name(self, val):
        return val

    @cas9core.dproperty
    def serial_set_chn(self):
        def action_sequence(cmd):
            #cmd.writeline('*IDN?')
            #val = cmd.readline()
            ##TODO PARSE
            #print(val)
            #if this is NOT called, then serial calls it automatically
            print("START BLOCK {0}".format(self.channel_name))
            cmd.block_remainder()
            print("DONE BLOCK {0}".format(self.channel_name))

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.parent.serial_id_check,
            name = 'set_chn',
            prefix = self.prefix_full,
        )
        return block

    @cas9core.dproperty
    def rf_frequency_set(self):
        default = self.ctree.setdefault('frequency_set', -1)
        rv = relay_values.RelayValueFloat(default)

        def cb(value):
            self.serial_freq_set()
            self.serial.run()
        rv.register(callback = self.reactor.cb_send_task(cb))

        self.cas_host(
            rv,
            'freq_set',
            writable = True,
        )
        return rv

    @cas9core.dproperty
    def serial_freq_set(self):
        def action_sequence(cmd):
            #cmd.writeline('*IDN?')
            #val = cmd.readline()
            ##TODO PARSE
            #print(val)
            #if this is NOT called, then serial calls it automatically
            print("FREQ SET")
            return
        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.serial_set_chn,
            name = 'freq_set',
            prefix = self.prefix_full,
        )
        self.serial.block_chain(block, self.serial_freq_RB)
        return block

    @cas9core.dproperty
    def rv_frequency_RB(self):
        default = self.ctree.setdefault('frequency_RB', -1, about = "frequency readback default (used when value unavailable)")
        rv = relay_values.RelayValueFloat(default)
        self.cas_host(
            rv,
            'freq_RB',
            writable = False,
        )
        return rv

    @cas9core.dproperty
    def serial_freq_RB(self):
        def action_sequence(cmd):
            print("FREQ RB")
            #cmd.writeline('')
            line = cmd.readline()
            #TODO parse
            self.rv_frequency_RB.value = len(line)

        block = self.serial.block_add(
            action_sequence,
            ordering = 10,
            parent   = self.serial_set_chn,
            name = 'freq_RB',
            prefix = self.prefix_full,
        )
        return block
