"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

from .. import cas9core
from .serial_base import (
    SerialSubBlock,
)

# from . import utilities


class GPIBAddressed(SerialSubBlock):
    @cas9core.dproperty
    def GPIB_addr(self, val):
        return val

    @cas9core.dproperty
    def SB_parent(self):
        return self.SB_addressed_block

    @cas9core.dproperty
    def rb_communicating(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb,
            name="COMM",
            interaction="report",
        )

        def pass_up(value):
            self.serial.rb_communicating.put(value)

        rb.register(callback=pass_up)
        return rb

    @cas9core.dproperty
    def SB_addressed_block(self):
        def action_sequence(cmd):
            cmd.writeline("++addr {0}".format(self.GPIB_addr))
            cmd.block_remainder()

        block = self.serial.block_add(
            action_sequence,
            ordering=0,
            name="addressed_block",
            prefix=self.prefix,
        )
        return block
