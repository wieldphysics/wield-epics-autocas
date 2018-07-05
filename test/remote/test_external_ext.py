"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals
import sys
import cas9epics
import declarative

from test_external_int import RVConnects

class Testers(cas9epics.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVConnects(
            name = 'TEST',
            subprefix = None,
            parent = self,
            remote = True,
        )

if __name__ == "__main__":
    Testers.cmdline(
        module_name_base = 'RVExternal',
    )

