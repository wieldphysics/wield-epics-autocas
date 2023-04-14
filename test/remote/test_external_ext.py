"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""

import sys
from wield.epics import autocas
from wield import declarative

from test_external_int import RVConnects


class Testers(autocas.CAS9Module):
    @declarative.dproperty
    def test(self):
        return RVConnects(
            name="TEST",
            subprefix=None,
            parent=self,
            remote=True,
        )


if __name__ == "__main__":
    Testers.cmdline(
        module_name_base="RVExternal",
    )
